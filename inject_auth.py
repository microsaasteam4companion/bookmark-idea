import os

root_dir = r"c:\Users\LENOVO\Downloads\bookmark-idea-main\bookmark-idea-main\landing-page"

auth_snippet = """
  <!-- Firebase & Auth Sync -->
  <script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js"></script>
  <script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-auth-compat.js"></script>
  <script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore-compat.js"></script>
  <script src="/firebase-config.js"></script>
  <script>
    if (!firebase.apps.length) {
        firebase.initializeApp(firebaseConfig);
    }
    const auth = firebase.auth();
    const db = firebase.firestore();

    function openAuthModal() { 
        if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
            const modal = document.getElementById('auth-modal');
            if(modal) modal.style.display = 'flex';
        } else {
            window.location.href = '/#download'; 
        }
    }
    
    function signOutUser() { auth.signOut().then(() => window.location.reload()); }
    
    function toggleUserDropdown(e) {
      if(e) e.stopPropagation();
      const dd = document.getElementById('user-dropdown');
      if(dd) dd.classList.toggle('active');
    }

    auth.onAuthStateChanged(user => {
      const signInBtn = document.getElementById('auth-signin-btn');
      const userMenu = document.getElementById('user-menu');
      const mobilePurchases = document.getElementById('mobile-purchases-link');
      
      if (user) {
        if(signInBtn) signInBtn.style.display = 'none';
        if(userMenu) {
            userMenu.style.display = 'flex';
            const avatar = document.getElementById('user-avatar');
            if(avatar) avatar.src = user.photoURL || 'https://ui-avatars.com/api/?name=' + encodeURIComponent(user.displayName || user.email);
            const name = document.getElementById('user-name');
            if(name) name.textContent = user.displayName || user.email.split('@')[0];
        }
        if(mobilePurchases) mobilePurchases.style.display = 'block';
      } else {
        if(signInBtn) signInBtn.style.display = 'block';
        if(userMenu) userMenu.style.display = 'none';
        if(mobilePurchases) mobilePurchases.style.display = 'none';
      }
    });

    window.addEventListener('click', () => {
        const dd = document.getElementById('user-dropdown');
        if(dd && dd.classList.contains('active')) dd.classList.remove('active');
    });
  </script>
"""

def inject_auth(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                # Skip files that already have complex auth logic if needed, 
                # but we'll try to be safe by checking for firebase-config.js
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                if "firebase-config.js" in content and "onAuthStateChanged" in content:
                    print(f"Auth already exists in {path}, skipping...")
                    continue
                
                if "</body>" in content:
                    updated_content = content.replace("</body>", f"{auth_snippet}\n</body>")
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(updated_content)
                    print(f"Injected Auth into {path}")

inject_auth(root_dir)
print("Auth injection complete.")
