
import sys
import os
try:
    from core.license_manager import LicenseManager
    lm = LicenseManager()
    print(f"HWID:{lm.get_hwid()}")
except ImportError as e:
    print(f"ERROR: {e}")
except Exception as e:
    print(f"FAIL: {e}")
