import os
import json
import re

blogs_dir = r"c:\Users\LENOVO\Downloads\bookmark-idea-main\bookmark-idea-main\landing-page\blogs"
files = [f for f in os.listdir(blogs_dir) if f.endswith(".html") and f != "index.html"]

for filename in files:
    path = os.path.join(blogs_dir, filename)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    title_match = re.search(r"<title>(.*?)</title>", content)
    title = title_match.group(1) if title_match else "CtrlSense Blog"
    
    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title.split(" - ")[0],
        "image": "https://ctrlsense.vercel.app/ctrlsense_logo.png",
        "author": {
            "@type": "Organization",
            "name": "CtrlSense"
        },
        "publisher": {
          "@type": "Organization",
          "name": "CtrlSense",
          "logo": {
            "@type": "ImageObject",
            "url": "https://ctrlsense.vercel.app/ctrlsense_logo.png"
          }
        },
        "datePublished": "2026-03-27",
        "description": f"Read about {title.split(' - ')[0]} on the CtrlSense blog. Deep dive into local AI and semantic search."
    }
    
    schema_html = f'\n  <script type="application/ld+json">\n  {json.dumps(schema, indent=2)}\n  </script>'
    
    if "</head>" in content:
        content = content.replace("</head>", schema_html + "\n</head>")
        
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Added Schema to {filename}")
