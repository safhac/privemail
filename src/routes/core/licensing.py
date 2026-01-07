import hashlib
import uuid
import subprocess
import platform
import sys

# SECRET SALT - CHANGE THIS BEFORE RELEASING!
SECRET_SEED = "LEGAL_DUCK_SECRET_V1"

def get_machine_fingerprint():
    """Generates unique ID based on hardware."""
    try:
        if sys.platform == 'win32':
            cmd = 'wmic csproduct get uuid'
            uuid_str = subprocess.check_output(cmd).decode().split('\n')[1].strip()
            return uuid_str
        elif sys.platform == 'darwin': # Mac
            cmd = "ioreg -d2 -c IOPlatformExpertDevice | awk -F\\\" '/IOPlatformUUID/{print $(NF-1)}'"
            uuid_str = subprocess.check_output(cmd, shell=True).decode().strip()
            return uuid_str
        else:
            return str(uuid.getnode())
    except Exception:
        return "GENERIC-" + platform.node()

def generate_short_machine_id():
    """Returns readable 8-char ID."""
    raw_id = get_machine_fingerprint()
    hashed = hashlib.sha256(raw_id.encode()).hexdigest().upper()
    return f"{hashed[:4]}-{hashed[4:8]}"

def generate_license_key(machine_id_short, product_tier="PRO"):
    """Creates a valid key: TIER-SIG1-SIG2"""
    raw_string = f"{machine_id_short}|{product_tier}|{SECRET_SEED}"
    signature = hashlib.sha256(raw_string.encode()).hexdigest().upper()
    return f"{product_tier}-{signature[:4]}-{signature[4:8]}"

def verify_license_key(user_key):
    """Verifies key against current machine."""
    try:
        parts = user_key.split('-')
        if len(parts) != 3: return False, None
        
        tier = parts[0]
        my_machine_id = generate_short_machine_id()
        expected_key = generate_license_key(my_machine_id, tier)
        
        return (user_key == expected_key), tier
    except:
        return False, None