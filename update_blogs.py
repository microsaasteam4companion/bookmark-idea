import os
import re

blogs_dir = r"c:\Users\LENOVO\Downloads\bookmark-idea-main\bookmark-idea-main\landing-page\blogs"
files = [f for f in os.listdir(blogs_dir) if f.endswith(".html") and f != "index.html"]

burger_html = """
    <button class="nav-burger" id="burger-btn">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
    </button>
  </nav>

  <div class="mobile-overlay" id="mobile-overlay"></div>
  <div class="mobile-menu" id="mobile-menu">
    <a href="../index.html#pipeline">How it works</a>
    <a href="../index.html#features">Features</a>
    <a href="../docs.html">Docs</a>
    <a href="index.html">Blogs</a>
    <a href="../index.html#download">Download</a>
  </div>
"""

mobile_css = """
    /* MOBILE MENU STYLES */
    .nav-burger { display:none; background:none; border:none; color:var(--ink); cursor:pointer; padding:8px; z-index:250; margin-left:auto; }
    .mobile-menu { position:fixed; top:0; right:-100%; width:280px; height:100vh; background:var(--bg2); z-index:245; padding:80px 32px; transition:0.4s; border-left:1px solid var(--border); display:flex; flex-direction:column; gap:24px; box-shadow:-10px 0 30px rgba(0,0,0,0.5); }
    .mobile-menu.active { right:0; }
    .mobile-menu a { font-size:18px; font-weight:500; color:var(--ink); text-decoration:none !important; }
    .mobile-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.6); z-index:240; opacity:0; pointer-events:none; transition:0.4s; backdrop-filter:blur(4px); }
    .mobile-overlay.active { opacity:1; pointer-events:auto; }
    @media (max-width: 768px) { .nav-mid { display:none !important; } .nav-burger { display:block; } }
"""

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

for filename in files:
    path = os.path.join(blogs_dir, filename)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. Add CSS before </style>
    if "</style>" in content:
        content = content.replace("</style>", mobile_css + "\n  </style>")
    
    # 2. Add Burger and Mobile Menu after </nav>
    if "</nav>" in content:
        content = content.replace("</nav>", burger_html)
        
    # 3. Add JS before </body>
    if "</body>" in content:
        content = content.replace("</body>", mobile_js + "\n</body>")
        
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Updated {filename}")
