import hashlib
import uuid
import subprocess
import platform
import sys
import logging

# Try to load the real secret from a file NOT in Git
try:
    from .private_constants import REAL_SECRET_SEED
except ImportError:
    # Fallback for Open Source users (Dummy seed)
    REAL_SECRET_SEED = "OPEN_SOURCE_DEV_BUILD"


def get_machine_fingerprint():
    """Generates unique ID based on hardware."""
    # (Keep your existing logic here, it is fine for this purpose)
    try:
        if sys.platform == 'win32':
            cmd = 'wmic csproduct get uuid'
            return subprocess.check_output(cmd).decode().split('\n')[1].strip()
        elif sys.platform == 'darwin':
            cmd = "ioreg -d2 -c IOPlatformExpertDevice | awk -F\\\" '/IOPlatformUUID/{print $(NF-1)}'"
            return subprocess.check_output(cmd, shell=True).decode().strip()
        else:
            return str(uuid.getnode())
    except Exception:
        return "GENERIC-" + platform.node()


def generate_short_machine_id():
    raw_id = get_machine_fingerprint()
    hashed = hashlib.sha256(raw_id.encode()).hexdigest().upper()
    return f"{hashed[:4]}-{hashed[4:8]}"


def generate_license_key(machine_id_short, product_tier="PRO"):
    # Use the loaded seed (Real or Dummy)
    raw_string = f"{machine_id_short}|{product_tier}|{REAL_SECRET_SEED}"
    signature = hashlib.sha256(raw_string.encode()).hexdigest().upper()
    return f"{product_tier}-{signature[:4]}-{signature[4:8]}"


def verify_license_key(user_key):
    """
    Verifies license. 
    Allows access AUTOMATICALLY if running from Source (Dev mode).
    Enforces check ONLY if running as Compiled/Frozen (Installer mode).
    """
    # 1. Check if we are running from Source (Python) or Installer (Frozen)
    is_compiled = getattr(sys, 'frozen', False)

    if not is_compiled:
        # Open Source / Dev Mode -> Always Valid
        return True, "DEV-MODE"

    # 2. If Compiled ($10 Installer), enforce the check
    try:
        parts = user_key.split('-')
        if len(parts) != 3:
            return False, None

        tier = parts[0]
        my_machine_id = generate_short_machine_id()

        # Generate the expected key using the Secret Seed bundled in the exe
        expected_key = generate_license_key(my_machine_id, tier)

        if user_key == expected_key:
            return True, tier
        else:
            return False, None
    except Exception as e:
        logging.error(f"License check failed: {e}")
        return False, None
