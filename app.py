"""
AI Document Assistant — Desktop App Entry Point.
Uses Flask + FlaskWebGui in app-mode for a native desktop experience.
"""

from __future__ import annotations
import os
import sys

# PyInstaller PyTorch DLL Resolution Fix (WinError 1114)
if hasattr(sys, '_MEIPASS'):
    os.environ["PATH"] = sys._MEIPASS + os.pathsep + os.environ.get("PATH", "")
    try:
        os.add_dll_directory(sys._MEIPASS)
    except Exception:
        pass

import base64
import os
import uuid

from flask import Flask, jsonify, request, send_from_directory
from flaskwebgui import FlaskUI
from dotenv import load_dotenv
from dodopayments import DodoPayments

# Load environment variables from .env
load_dotenv()

from core.config import UPLOAD_DIR
from core.embeddings import VectorStore
from core.extractor import extract_text
from core import metadata


# ── Flask App ────────────────────────────────────────────────────────
app = Flask(__name__, static_folder="frontend", static_url_path="")
vector_store: VectorStore | None = None

# ── Dodo Payments Client ─────────────────────────────────────────────
dodo_api_key = os.getenv("DODO_PAYMENTS_API_KEY")
if dodo_api_key:
    dodo_client = DodoPayments(
        bearer_token=dodo_api_key,
        environment=os.getenv("DODO_ENVIRONMENT", "test_mode")
    )
else:
    dodo_client = None
    print("Warning: DODO_PAYMENTS_API_KEY not found. Payments will be disabled.")


# ── Serve Frontend ───────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")


# ── API Routes ───────────────────────────────────────────────────────
@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Decode a base64 file, extract text, embed, and store metadata."""
    try:
        from core.license import is_pro_active
        docs = metadata.get_all_documents()
        if len(docs) >= 25 and not is_pro_active():
             return jsonify({"success": False, "error": "Document limit reached (25 files). Upgrade to Pro for unlimited uploads!"})

        data = request.get_json()
        filename = data.get("filename", "")
        base64_content = data.get("base64_content", "")

        doc_id = uuid.uuid4().hex
        file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{filename}")

        # Decode & save
        raw = base64.b64decode(base64_content)
        with open(file_path, "wb") as f:
            f.write(raw)

        # Extract text
        text = extract_text(file_path)
        if not text.strip():
            return jsonify({"success": False, "error": "Could not extract any text from this file."})

        # Embed
        vector_store.add_document(
            doc_id=doc_id,
            text=text,
            metadata={"filename": filename},
        )

        # Generate Auto-Summary
        try:
            from core.summarizer import summarizer
            doc_summary = summarizer.summarize(text)
        except Exception as e:
            print(f"Summarizer error: {e}")
            doc_summary = "Summary unavailable."

        # Metadata
        metadata.add_document(doc_id, filename, file_path, summary=doc_summary)

        return jsonify({"success": True, "doc_id": doc_id, "filename": filename})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/payments/checkout", methods=["POST"])
def create_checkout_session():
    """Create a Dodo Payments checkout session for the Pro plan."""
    try:
        product_id = os.getenv("DODO_PRODUCT_ID")
        if not product_id:
            return jsonify({"success": False, "error": "DODO_PRODUCT_ID not configured in .env"})

        # The redirect URL should point to the web dashboard
        data = request.get_json() or {}
        redirect_url = data.get("redirect_url", "https://ctrlsense.vercel.app/purchases.html")

        # Checkout session via SDK
        if not dodo_client:
            return jsonify({
                "success": False, 
                "error": "Payments are not configured in this app version. Please contact support or the administrator."
            })

        session = dodo_client.checkout_sessions.create(
            product_cart=[
                {
                    "product_id": product_id,
                    "quantity": 1
                }
            ],
            return_url=redirect_url
        )
        
        # In test mode, we construct the URL but rely on the SDK's session if available
        # The user provided link: https://test.checkout.dodopayments.com/buy/pdt_...
        # Note: Static links use 'redirect_url', but SDK uses 'return_url'
        checkout_url = f"https://test.checkout.dodopayments.com/buy/{product_id}?quantity=1&redirect_url={redirect_url}"
        
        # If the session object has a checkout_url, use it
        if hasattr(session, 'checkout_url') and session.checkout_url:
            checkout_url = session.checkout_url

        return jsonify({"success": True, "checkout_url": checkout_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/search", methods=["POST"])
def search():
    """Embed query and return the top matching documents."""
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        file_type = data.get("file_type", "all").lower()   # "all", "pdf", "txt"
        sort_by = data.get("sort_by", "relevance")          # "relevance", "date_newest", "date_oldest", "name"

        if not query:
            return jsonify({"success": False, "error": "Please enter a search query."})

        hits = vector_store.search(query, top_k=5)

        results = []
        for hit in hits:
            doc = metadata.get_document(hit["id"])
            results.append({
                "id": hit["id"],
                "filename": doc["filename"] if doc else "Unknown",
                "snippet": hit["text"][:300],
                "score": round(1 - hit["distance"], 4),
                "uploaded_at": doc.get("uploaded_at", "") if doc else "",
            })

        # ── Filter out low-confidence results ──
        MIN_SCORE = 0.25
        results = [r for r in results if r["score"] >= MIN_SCORE]

        # ── Filter by file type (optional) ──
        if file_type and file_type != "all":
            ext = f".{file_type}"
            results = [r for r in results if r["filename"].lower().endswith(ext)]

        # ── Sort results (optional, default = relevance / score desc) ──
        if sort_by == "date_newest":
            results.sort(key=lambda r: r.get("uploaded_at", ""), reverse=True)
        elif sort_by == "date_oldest":
            results.sort(key=lambda r: r.get("uploaded_at", ""))
        elif sort_by == "name":
            results.sort(key=lambda r: r.get("filename", "").lower())
        # else: "relevance" — already sorted by score from vector_store

        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/documents", methods=["GET"])
def get_all_documents():
    """Return the full document library."""
    try:
        docs = metadata.get_all_documents()
        filenames = [d.get("filename") for d in docs]
        print(f"[API] get_all_documents: {len(docs)} found -> {filenames}")
        return jsonify({"success": True, "documents": docs})
    except Exception as e:
        print(f"[API] get_all_documents error: {e}")
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/documents/<doc_id>/content", methods=["GET"])
def get_document_content(doc_id):
    """Read the raw original file from disk and return its text."""
    try:
        doc = metadata.get_document(doc_id)
        if not doc or not os.path.exists(doc.get("file_path", "")):
            return jsonify({"success": False, "error": "Document not found on disk."})
            
        text = extract_text(doc["file_path"])
        return jsonify({"success": True, "filename": doc["filename"], "content": text})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/documents/<doc_id>", methods=["DELETE"])
def delete_document(doc_id):
    """Remove a document from vector store, metadata, and disk."""
    try:
        doc = metadata.get_document(doc_id)

        # Vector store
        vector_store.delete_document(doc_id)

        # Metadata
        metadata.delete_document(doc_id)

        # Disk
        if doc and os.path.exists(doc.get("file_path", "")):
            os.remove(doc["file_path"])

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/settings/create-shortcut", methods=["POST"])
def create_shortcut():
    """Create a desktop shortcut using Windows Scripting."""
    from core.license import is_pro_active
    if not is_pro_active():
        return jsonify({"success": False, "error": "Shortcuts require a Pro License."})

    try:
        import subprocess
        desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
        lnk_path = os.path.join(desktop, "CtrlSense.lnk")
        
        # Resolve best target
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Inside portable build, bat launcher is next to app.py
        bat_launcher = os.path.join(base_dir, "CtrlSense Launcher.bat")
        
        if os.path.exists(bat_launcher):
            target_exe = bat_launcher
            args = ""
        else:
            # Fallback for dev mode
            target_exe = sys.executable
            args = f'"{os.path.abspath(__file__)}"'

        # PowerSell script setup
        script = f"""
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("{lnk_path}")
        $Shortcut.TargetPath = "{target_exe}"
        $Shortcut.Arguments = "{args}"
        $Shortcut.WorkingDirectory = "{os.path.dirname(target_exe)}"
        $Shortcut.IconLocation = "{sys.executable}"
        $Shortcut.Save()
        """
        subprocess.run(["powershell", "-Command", script], capture_output=True)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/settings/choose-folder", methods=["POST"])
def choose_folder():
    """Open a native Windows Folder Selection Dialog using PowerShell."""
    from core.license import is_pro_active
    if not is_pro_active():
        return jsonify({"success": False, "error": "Watch Folders require a Pro License."})

    try:
        import subprocess
        script = """
        Add-Type -AssemblyName System.Windows.Forms
        $FolderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
        $FolderBrowser.Description = "Select Watch Folder"
        [void]$FolderBrowser.ShowDialog()
        $FolderBrowser.SelectedPath
        """
        # Run PowerShell without opening a console window
        result = subprocess.run(["powershell", "-Command", script], capture_output=True, text=True)
        folder_path = result.stdout.strip()
        
        if folder_path:
             # Dynamically update the background watcher
             try:
                 from core.watcher import update_watched_dir
                 update_watched_dir(folder_path)
             except Exception as e:
                 print(f"Watcher reload failed: {e}")
                 
             return jsonify({"success": True, "folder_path": folder_path})
        return jsonify({"success": False, "error": "No folder selected"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/settings/toggle-startup", methods=["POST"])
def toggle_startup():
    """Add/Remove application from Windows Startup registry."""
    try:
        data = request.get_json()
        enabled = data.get("enabled", False)
        
        import winreg
        key = winreg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        target_exe = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)

        registry_key = winreg.OpenKey(key, key_path, 0, winreg.KEY_WRITE)
        if enabled:
            winreg.SetValueEx(registry_key, "CtrlSense", 0, winreg.REG_SZ, target_exe)
        else:
            try:
                winreg.DeleteValue(registry_key, "CtrlSense")
            except FileNotFoundError:
                pass
        winreg.CloseKey(registry_key)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})



# ── Shell Integration & CLI ──────────────────────────────────────────
def handle_cli_args(vector_store):
    """Check for file paths passed as arguments and add them to the brain."""
    if len(sys.argv) > 1:
        # Ignore script name, flags
        args = [arg for arg in sys.argv[1:] if not arg.startswith('-')]
        for path in args:
            if os.path.isfile(path) and path.lower().endswith(('.pdf', '.txt')):
                print(f"[SHELL] Adding file from command line: {path}")
                try:
                    filename = os.path.basename(path)
                    text = extract_text(path)
                    if text.strip():
                        doc_id = uuid.uuid4().hex
                        # Copy to upload dir
                        import shutil
                        dest = os.path.join(UPLOAD_DIR, f"{doc_id}_{filename}")
                        shutil.copy2(path, dest)
                        
                        vector_store.add_document(doc_id, text, {"filename": filename})
                        
                        # Summary
                        try:
                            from core.summarizer import summarizer
                            summary = summarizer.summarize(text)
                        except:
                            summary = "Summary unavailable."
                            
                        metadata.add_document(doc_id, filename, dest, summary=summary)
                        print(f"[SHELL] Successfully added: {filename}")
                except Exception as e:
                    print(f"[SHELL] Error adding file: {e}")

def setup_windows_context_menu():
    """Adds 'Add to CtrlSense Brain' to the Windows right-click menu."""
    try:
        import winreg
        # Get path to current script or exe
        if hasattr(sys, 'frozen'):
            exe_path = sys.executable
        else:
            # For portable .bat, we want the .bat or the python command
            # But the simplest is to point to the bat in the portable folder
            # For now, let's use the current python + script path
            exe_path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'

        # Key: * (all files)
        key_path = r"*\shell\CtrlSense"
        
        # 1. Create main key
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\\" + key_path) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "Add to CtrlSense Brain")
            # Optional: Add icon if we have one
            # winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, exe_path)

        # 2. Create command key
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\\" + key_path + r"\command") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, f'{exe_path} "%1"')
            
        print("[INIT] Windows Context Menu integrated successfully.")
    except Exception as e:
        print(f"[INIT] Context Menu setup failed: {e}")

# ── Launch ───────────────────────────────────────────────────────────

def setup_global_hotkey():
    try:
        import keyboard
        import pygetwindow as gw
        
        def bring_to_front():
            print("[HOTKEY] Trigger detected!")
            try:
                all_windows = gw.getAllWindows()
                target = None
                for w in all_windows:
                    if 'ctrlsense' in w.title.lower() or 'ai document' in w.title.lower():
                        print(f"[HOTKEY] Found matching window: {w.title}")
                        target = w
                        break
                
                if target:
                    if target.isMinimized:
                        target.restore()
                    target.activate()
                    print("[HOTKEY] Window brought to front.")
                else:
                    print("[HOTKEY] Error: Could not find application window.")
            except Exception as e:
                print(f"[HOTKEY] bring_to_front error: {e}")

        # Ctrl+Shift+D — safe cross-app hotkey
        keyboard.add_hotkey('ctrl+shift+d', bring_to_front)
        print("[INIT] Global Hotkey registered: Ctrl+Shift+D")
    except Exception as e:
        print(f"[INIT] Hotkey setup failed: {e}")

@app.route("/api/settings/license", methods=["GET", "POST", "DELETE"])
def manage_license():
    """Read, update or delete Pro license verification status."""
    import importlib, core.license
    importlib.reload(core.license)
    from core.license import is_pro_active, activate_license, deactivate_license
    
    if request.method == "DELETE":
        deactivate_license()
        return jsonify({"success": True, "is_pro": False})

    if request.method == "POST":
        data = request.get_json() or {}
        key = data.get("key", "")
        if activate_license(key):
            return jsonify({"success": True, "is_pro": True})
        return jsonify({"success": False, "error": "Invalid License Key."})

    # GET
    return jsonify({"success": True, "is_pro": is_pro_active()})

if __name__ == "__main__":
    print("[INIT] Starting AI Document Assistant ...")
    vector_store = VectorStore()
    
    # Setup Shell Integrations
    setup_windows_context_menu()
    handle_cli_args(vector_store)

    # Start background folder watcher
    from core.watcher import start_watcher
    start_watcher(vector_store)
    
    # Setup Spotlight hotkey
    setup_global_hotkey()

    print("[INIT] Opening desktop window ...")
    FlaskUI(
        app=app,
        server="flask",
        width=1100,
        height=750,
    ).run()
