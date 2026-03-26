import os

root_dir = r"c:\Users\LENOVO\Downloads\bookmark-idea-main\bookmark-idea-main\landing-page"

def update_links(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                updated_content = content.replace('href="blogs/index.html"', 'href="blogs/"')
                updated_content = updated_content.replace('href="../blogs/index.html"', 'href="../blogs/"')
                updated_content = updated_content.replace('href="index.html"', 'href="./"')
                
                if content != updated_content:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(updated_content)
                    print(f"Updated links in {path}")

update_links(root_dir)
