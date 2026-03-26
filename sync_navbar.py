import os
import re

root_dir = r"c:\Users\LENOVO\Downloads\bookmark-idea-main\bookmark-idea-main"

navbar_html = """
  <nav id="nav">
    <a href="/" class="nav-logo">
      <div class="nav-logo-box" style="background:transparent; overflow:hidden;"><img src="/ctrlsense_logo.png"
          style="width:100%;height:100%;border-radius:inherit;object-fit:cover; transform:scale(1.8);"
          alt="CtrlSense Logo"></div>
      CtrlSense
    </a>
    <div class="nav-mid">
      <a href="/#pipeline">How it works</a>
      <a href="/#features">Features</a>
      <a href="/docs">Docs</a>
      <a href="/blogs">Blogs</a>
      <a href="/#download">Download</a>
    </div>
    <div class="nav-right" style="display: flex; align-items: center; gap: 12px;">
      <button class="theme-btn" id="theme-btn" title="Toggle light/dark">
        <svg id="theme-icon" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="5" />
          <line x1="12" y1="1" x2="12" y2="3" />
          <line x1="12" y1="21" x2="12" y2="23" />
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
          <line x1="1" y1="12" x2="3" y2="12" />
          <line x1="21" y2="12" x2="23" y2="12" />
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </svg>
      </button>

      <!-- Auth Buttons -->
      <button class="auth-btn" id="auth-signin-btn" onclick="openAuthModal()">Sign In</button>
      <div class="user-menu" id="user-menu" style="display: none;" onclick="toggleUserDropdown(event)">
        <img class="user-avatar" id="user-avatar" src="" alt="User">
        <span class="user-name" id="user-name"></span>
        <div class="user-dropdown" id="user-dropdown">
          <a href="/purchases">🛒 My Purchases</a>
          <div class="dd-divider"></div>
          <button onclick="signOutUser()">🚪 Sign Out</button>
        </div>
      </div>
      <a href="/#download" class="nav-btn nav-btn-solid">Download Now</a>

      <button class="nav-burger" id="burger-btn">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
      </button>
    </div>
  </nav>

  <div class="mobile-overlay" id="mobile-overlay"></div>
  <div class="mobile-menu" id="mobile-menu">
    <a href="/#pipeline">How it works</a>
    <a href="/#features">Features</a>
    <a href="/docs">Docs</a>
    <a href="/blogs">Blogs</a>
    <a href="/purchases" id="mobile-purchases-link" style="display: none;">My Purchases</a>
    <a href="/#download" id="mobile-dl-link">Download Now</a>
    <div id="mobile-auth-section" style="margin-top: auto; padding-top: 24px; border-top: 1px solid var(--border);">
    </div>
  </div>
"""

def apply_navbar(directory):
    target_files = ["index.html", "docs.html", "purchases.html", "privacy.html", "terms.html"]
    
    for root, dirs, files in os.walk(directory):
        if any(x in root for x in [".git", "core", "frontend", "landing-page"]): continue
        
        for file in files:
            if file.endswith(".html"):
                path = os.path.join(root, file)
                if file in target_files or "blogs" in root:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # 1. Replace nav block
                    content = re.sub(r'<nav.*?</nav>', navbar_html, content, flags=re.DOTALL)
                    
                    # 2. Add logo CSS fix to existing style block or head
                    logo_css = """
    .nav-logo-box { width:24px; height:24px; border-radius:6px; display:flex; align-items:center; justify-content:center; overflow:hidden; }
    .nav-logo-box img { width:100%; height:100%; object-fit:cover; }
"""
                    if logo_css not in content:
                        if "</style>" in content:
                            content = content.replace("</style>", logo_css + "\n  </style>")
                        elif "</head>" in content:
                            content = content.replace("</head>", f"<style>\n  {logo_css}\n  </style>\n</head>")
                    
                    # 3. Clean blog card links ONLY in blogs/index.html
                    if file == "index.html" and "blogs" in root:
                        content = re.sub(r'href="([^"]+)\.html"', r'href="/blogs/\1"', content)
                        # Fix for Home link if it got messed up
                        content = content.replace('href="/blogs//"', 'href="/"')
                        content = content.replace('href="/blogs/docs"', 'href="/docs"')
                        content = content.replace('href="/blogs/blogs"', 'href="/blogs"')
                        content = content.replace('href="/blogs/purchases"', 'href="/purchases"')

                    with open(path, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"Applied navbar & logo fix to {path}")

apply_navbar(root_dir)
print("All pages synchronized with logo fix.")
