import os
import sys
import shutil
import urllib.request
import zipfile
import subprocess

def build():
    print("[PORTABLE BUILD] Starting...")
    build_dir = r"d:\Projects\Ai DOC\portable_build"
    app_base = "CtrlSense-Portable"
    out_dir = os.path.join(build_dir, app_base)
    
    if os.path.exists(build_dir):
        try:
            shutil.rmtree(build_dir)
        except Exception as e:
            print(f"[PORTABLE BUILD] Warning: Could not fully clear old build_dir: {e}. Proceeding with file overrides...")
    os.makedirs(out_dir, exist_ok=True)
    
    print("[PORTABLE BUILD] Downloading Embedded Python 3.12...")
    py_zip = os.path.join(build_dir, "python.zip")
    urllib.request.urlretrieve("https://www.python.org/ftp/python/3.12.2/python-3.12.2-embed-amd64.zip", py_zip)
    
    with zipfile.ZipFile(py_zip, 'r') as z:
        z.extractall(out_dir)
        
    print("[PORTABLE BUILD] Modifying python312._pth to enable site-packages...")
    pth_file = os.path.join(out_dir, "python312._pth")
    with open(pth_file, 'r') as f:
         lines = f.readlines()
    with open(pth_file, 'w') as f:
         for line in lines:
             if line.strip() == "#import site":
                 f.write("import site\n")
             else:
                 f.write(line)
                 
    print("[PORTABLE BUILD] Downloading get-pip.py...")
    pip_script = os.path.join(out_dir, "get-pip.py")
    urllib.request.urlretrieve("https://bootstrap.pypa.io/get-pip.py", pip_script)
    
    print("[PORTABLE BUILD] Installing pip into Embedded Python...")
    py_exe = os.path.join(out_dir, "python.exe")
    subprocess.check_call([py_exe, pip_script])
    
    print("[PORTABLE BUILD] Installing requirements one by one...")
    reqs_path = os.path.join(os.path.dirname(build_dir), "requirements.txt")
    with open(reqs_path, 'r') as f:
        deps = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    for dep in deps:
        print(f"[PORTABLE BUILD] Installing {dep}...")
        cmd = [py_exe, "-m", "pip", "install", dep]
        if "torch" in dep.lower() or "sentence-transformers" in dep.lower():
             cmd += ["--extra-index-url", "https://download.pytorch.org/whl/cpu"]
        if "pywebview" in dep.lower() or "easyocr" in dep.lower():
             cmd += ["--only-binary=:all:"]
        try:
            subprocess.check_call(cmd)
        except Exception as e:
            print(f"[PORTABLE BUILD] ERROR: Failed to install {dep}: {e}")
            # Continue to see if others fail too
    
    print("[PORTABLE BUILD] Copying application files...")
    # Copy app.py, core, frontend
    src = r"d:\Projects\Ai DOC"
    shutil.copy2(os.path.join(src, "app.py"), out_dir)
    shutil.copytree(os.path.join(src, "core"), os.path.join(out_dir, "core"))
    shutil.copytree(os.path.join(src, "frontend"), os.path.join(out_dir, "frontend"))
    
    print("[PORTABLE BUILD] Creating Launcher BAT...")
    bat_file = os.path.join(out_dir, "CtrlSense Launcher.bat")
    with open(bat_file, "w") as f:
         f.write("@echo off\n")
         f.write("echo Starting CtrlSense AI Engine...\n")
         f.write('"%~dp0python.exe" "%~dp0app.py"\n')
         f.write("pause\n")
         
    print("[PORTABLE BUILD] Compressing final zip payload...")
    zip_path = os.path.join(src, "landing-page", "AiDocumentAssistant-Windows.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
        
    shutil.make_archive(zip_path.replace(".zip", ""), 'zip', build_dir)
    print(f"[PORTABLE BUILD] Complete! ZIP generated at {zip_path}")

if __name__ == '__main__':
    build()
