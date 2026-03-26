import os
import re

root_dir = r"c:\Users\LENOVO\Downloads\bookmark-idea-main\bookmark-idea-main"

# The complete Navbar CSS extracted from index.html
navbar_css = """
    /* SYNCED NAVBAR CSS */
    :root {
      --bg: #141419; --bg2: #1c1c23; --surface: #1e1e27; --border: rgba(255, 255, 255, 0.07);
      --ink: #e4e4f0; --ink2: #9191a8; --accent: #a78bfa; --font: 'Inter', sans-serif;
    }
    nav { position: fixed; top: 0; left: 0; right: 0; z-index: 200; height: 56px; display: flex; align-items: center; padding: 0 32px; transition: all 0.25s; background: rgba(20, 20, 25, 0.88); border-bottom: 1px solid var(--border); backdrop-filter: blur(20px); }
    .nav-logo { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 600; color: var(--ink); text-decoration: none; }
    .nav-logo-box { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; overflow: hidden; }
    .nav-logo-box img { width: 100%; height: 100%; object-fit: cover; transform: scale(1.8); }
    .nav-mid { flex: 1; display: flex; justify-content: center; gap: 2px; }
    .nav-mid a { font-size: 13.5px; color: var(--ink2); text-decoration: none; padding: 5px 12px; border-radius: 6px; transition: 0.15s; }
    .nav-mid a:hover { color: var(--ink); background: var(--bg2); }
    .nav-right { display: flex; align-items: center; gap: 8px; }
    .auth-btn { background: var(--accent); color: #fff; border: none; padding: 8px 18px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; transition: 0.2s; }
    .auth-btn:hover { filter: brightness(1.15); transform: translateY(-1px); }
    .user-menu { position: relative; display: flex; align-items: center; gap: 8px; cursor: pointer; }
    .user-avatar { width: 32px; height: 32px; border-radius: 50%; border: 2px solid var(--accent); object-fit: cover; }
    .user-name { font-size: 13px; font-weight: 600; color: var(--ink); max-width: 100px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .user-dropdown { position: absolute; top: 44px; right: 0; background: #1a1a24; border: 1px solid var(--border); border-radius: 10px; min-width: 180px; box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4); display: none; overflow: hidden; }
    .user-dropdown.active { display: block; }
    .user-dropdown a, .user-dropdown button { display: block; width: 100%; text-align: left; padding: 12px 16px; font-size: 13px; color: #c8c8d8; background: none; border: none; cursor: pointer; text-decoration: none; transition: 0.15s; }
    .user-dropdown a:hover, .user-dropdown button:hover { background: rgba(167, 139, 250, 0.1); color: #fff; }
    .user-dropdown .dd-divider { height: 1px; background: rgba(255, 255, 255, 0.06); margin: 4px 0; }
    .theme-btn { background: none; border: none; color: var(--ink2); cursor: pointer; padding: 6px; border-radius: 6px; transition: 0.2s; display: flex; align-items: center; }
    .theme-btn svg { width: 18px; height: 18px; fill: currentColor; }
    .nav-burger { display: none; background: none; border: none; color: var(--ink); cursor: pointer; padding: 8px; z-index: 250; }
    .mobile-menu { position: fixed; top: 0; right: -100%; width: 280px; height: 100vh; background: var(--bg2); z-index: 245; padding: 80px 32px; transition: 0.4s; border-left: 1px solid var(--border); display: flex; flex-direction: column; gap: 24px; box-shadow: -10px 0 30px rgba(0,0,0,0.5); }
    .mobile-menu.active { right: 0; }
    .mobile-menu a { font-size: 18px; color: var(--ink); text-decoration: none; }
    .mobile-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 240; opacity: 0; pointer-events: none; transition: 0.4s; backdrop-filter: blur(4px); }
    .mobile-overlay.active { opacity: 1; pointer-events: auto; }
    @media(max-width:768px) { .nav-mid { display: none !important; } .nav-burger { display: block; } .auth-btn, .nav-btn-solid { display: none !important; } }
    .nav-btn-solid { background: var(--ink); color: var(--bg); padding: 6px 16px; border-radius: 7px; font-size: 13px; font-weight: 500; text-decoration: none; }
"""

navbar_html = """
  <nav id="nav">
    <a href="/" class="nav-logo">
      <div class="nav-logo-box" style="background:transparent; overflow:hidden;"><img src="/ctrlsense_logo.png"
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
          <circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" /><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" /><line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y2="12" x2="23" y2="12" /><line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </svg>
      </button>

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
    <div id="mobile-auth-section" style="margin-top: auto; padding-top: 24px; border-top: 1px solid var(--border);"></div>
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
                    
                    # 2. Inject complete CSS block
                    if '<style>' in content:
                        # Replace generic navbar styles with the extracted ones
                        # We try to find where the nav styles end
                        content = content.replace("<style>", f"<style>\n{navbar_css}\n")
                    
                    # 3. Fix blog card links only in blogs/index.html
                    if file == "index.html" and "blogs" in root:
                        content = re.sub(r'href="([^"]+)\.html"', r'href="/blogs/\1"', content)
                        content = content.replace('href="/blogs//"', 'href="/"')
                        content = content.replace('href="/blogs/docs"', 'href="/docs"')
                        content = content.replace('href="/blogs/blogs"', 'href="/blogs"')
                        content = content.replace('href="/blogs/purchases"', 'href="/purchases"')

                    with open(path, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"Applied full navbar fix to {path}")

apply_navbar(root_dir)
print("Site-wide navbar synchronization complete.")
