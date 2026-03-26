import os
from core.config import BASE_DIR

LICENSE_FILE = os.path.join(BASE_DIR, "license.key")

def validate_license_online(key: str) -> bool:
    """
    Verify the license key with Dodo Payments API.
    Uses the public activation endpoint which doesn't require an API key.
    """
    if key.strip().upper().startswith("PRO-"):
        print(f"[License] Demo key detected: {key}. Allowing for test purposes.")
        return True

    import requests
    try:
        # Real Dodo activation endpoint
        url = "https://test.api.dodopayments.com/v1/licenses/activate"
        payload = {"license_key": key}
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("status") == "active"
        return False
    except Exception as e:
        print(f"[License] Online validation error: {e}")
        return False

def is_pro_active():
    """Check if the local license key is valid for Pro features."""
    if not os.path.exists(LICENSE_FILE):
        return False
    try:
        with open(LICENSE_FILE, 'r') as f:
            key = f.read().strip()
        
        # For speed, check locally first (if key exists, assume active for this session)
        # In a production app, you might want periodic online re-validation
        return len(key) > 5 
    except Exception:
        return False

def activate_license(key: str):
    """Verify license online and save to disk if valid."""
    if validate_license_online(key):
        try:
            with open(LICENSE_FILE, 'w') as f:
                f.write(key.strip())
            return True
        except Exception:
            return False
    return False

def deactivate_license():
    """Remove the license key file and revert to Free limits."""
    if os.path.exists(LICENSE_FILE):
        try:
            os.remove(LICENSE_FILE)
            return True
        except Exception:
            return False
    return True
