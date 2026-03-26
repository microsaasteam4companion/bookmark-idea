import zipfile
import os

def zipdir(path, ziph):
    # ziph is zipfile handle
    parent_folder = os.path.basename(path)
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            # Create a relative path that starts with the parent folder name
            rel_path = os.path.join(parent_folder, os.path.relpath(file_path, path))
            ziph.write(file_path, rel_path)

if __name__ == '__main__':
    src = r'd:\Projects\Ai DOC\portable_build\CtrlSense-Portable'
    dst = r'd:\Projects\Ai DOC\landing-page\AiDocumentAssistant-Windows.zip'
    
    print(f"Creating ZIP from {src} to {dst}...")
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
        zipdir(src, zipf)
    print("ZIP creation complete!")
