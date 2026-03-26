import os
import re

root_dir = r"c:\Users\LENOVO\Downloads\bookmark-idea-main\bookmark-idea-main\landing-page"

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
          <a href="/purchases.html">🛒 My Purchases</a>
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
    <a href="/purchases.html" id="mobile-purchases-link" style="display: none;">My Purchases</a>
    <a href="/#download" id="mobile-dl-link">Download Now</a>
    <div id="mobile-auth-section" style="margin-top: auto; padding-top: 24px; border-top: 1px solid var(--border);">
       <!-- Auth content injected via JS -->
    </div>
  </div>
"""

def apply_navbar(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 1. Replace nav block
                content = re.sub(r'<nav.*?</nav>', navbar_html, content, flags=re.DOTALL)
                
                # 2. Add/replace mobile components
                content = re.sub(r'<div class="mobile-overlay".*?</div>', '', content, flags=re.DOTALL)
                content = re.sub(r'<div class="mobile-menu".*?</div>', '', content, flags=re.DOTALL)
                
                # 3. Ensure the CSS for .nav-right exists
                if ".nav-right {" not in content:
                    mobile_css = """
    .nav-right { display: flex; align-items: center; gap: 12px; }
    .nav-burger { display:none; background:none; border:none; color:#fff; cursor:pointer; padding:8px; z-index:250; }
    .mobile-menu { position:fixed; top:0; right:-100%; width:280px; height:100vh; background:#1c1c23; z-index:245; padding:80px 32px; transition:0.4s; border-left:1px solid rgba(255,255,255,0.07); display:flex; flex-direction:column; gap:24px; box-shadow:-10px 0 30px rgba(0,0,0,0.5); }
    .mobile-menu.active { right:0; }
    .mobile-menu a { font-size:18px; color:#fff; text-decoration:none !important; }
    .mobile-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.6); z-index:240; opacity:0; pointer-events:none; transition:0.4s; backdrop-filter:blur(4px); }
    .mobile-overlay.active { opacity:1; pointer-events:auto; }
    @media (max-width: 768px) { .nav-mid { display:none !important; } .nav-burger { display:block; } .auth-btn, .nav-btn-solid { display:none !important; } }
"""
                    if "</style>" in content:
                        content = content.replace("</style>", mobile_css + "\n  </style>")

                # 4. Ensure toggle script exists
                if "toggleMenu" not in content:
                    mobile_js = """
  <script>
    const burgerBtn = document.getElementById('burger-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    const mobileOverlay = document.getElementById('mobile-overlay');
    function toggleMenu() {
      mobileMenu.classList.toggle('active');
      mobileOverlay.classList.toggle('active');
      document.body.style.overflow = mobileMenu.classList.contains('active') ? 'hidden' : '';
    }
    if(burgerBtn) burgerBtn.addEventListener('click', toggleMenu);
    if(mobileOverlay) mobileOverlay.addEventListener('click', toggleMenu);
    mobileMenu.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => { if (mobileMenu.classList.contains('active')) toggleMenu(); });
    });
  </script>
"""
                    if "</body>" in content:
                        content = content.replace("</body>", mobile_js + "\n</body>")

                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Applied navbar to {path}")

apply_navbar(root_dir)
print("All pages synchronized.")
