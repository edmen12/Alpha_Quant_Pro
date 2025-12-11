
import subprocess
import hashlib
import platform
import logging
import os
import hmac
import struct

class LicenseManager:
    """
    Offline HWID Binding.
    Uses HMAC-SHA256(HWID, SECRET_KEY) to verify activation codes.
    MUST be compiled to .pyd to protect SECRET_KEY.
    """
    
    # --- SECURITY CORE ---
    # This key MUST remain secret. Changing it invalidates all keys.
    # In production, use a long random string.
    _SECRET = b"ALPHA_QUANT_PRO_V2_SECRET_KEY_8829"
    
    # --- ADMIN NOTIFICATION CONFIG ---
    # Embedded Token (Protected by Cython compilation)
    _BOT_TOKEN = "8312244017:AAENlYnUerAVYl9c1UAfoBmG5cq8hSJd3qA"
    _ADMIN_ID = "6759594496"
    
    def __init__(self):
        self.logger = logging.getLogger("LicenseManager")
        import requests 
        self.requests = requests # Lazy import or specific assignment
        
        # Use PathManager for writable location (Robust Import)
        try:
            try:
                from path_manager import PathManager
            except ImportError:
                # Try adding parent directory to path
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from path_manager import PathManager
                
            self.LICENSE_FILE = str(PathManager.get_app_data_dir() / "license.key")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.LICENSE_FILE), exist_ok=True)
            
        except ImportError:
            # Fallback for dev/test only if PathManager is absolutely missing
            self.logger.warning("PathManager not found. using local directory for license.")
            self.LICENSE_FILE = "license.key"

    def send_registration_request(self, hwid: str) -> bool:
        """
        Sends the HWID to Admin via Telegram.
        """
        try:
            msg = f"🔥 *NEW ACTIVATION REQUEST*\n\n💻 *HWID*: `{hwid}`\n\nGenerate Key:\n`/keygen {hwid}`"
            url = f"https://api.telegram.org/bot{self._BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": self._ADMIN_ID,
                "text": msg,
                "parse_mode": "Markdown"
            }
            # Use short timeout to not block UI
            resp = self.requests.post(url, json=payload, timeout=5)
            return resp.status_code == 200
        except Exception as e:
            self.logger.error(f"Failed to send HWID: {e}")
            return False
        
    def get_hwid(self) -> str:
        """
        Generates a unique Hardware ID based on Motherboard UUID.
        Returns a short simplified hash for user friendliness.
        """
        try:
            raw_id = ""
            # 1. Try Windows WMIC (Motherboard UUID)
            if platform.system() == "Windows":
                try:
                    cmd = "wmic csproduct get uuid"
                    output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
                    lines = output.split('\n')
                    if len(lines) > 1:
                        raw_id = lines[1].strip()
                except:
                    pass
            
            # 2. Key Fallback: CPU Info
            if not raw_id or raw_id == "":
                uname = platform.uname()
                raw_id = f"{uname.node}-{uname.machine}-{uname.processor}"
                
            # Hash it to standard length
            return hashlib.sha256(raw_id.encode()).hexdigest().upper()[:16] # 16 chars sufficient
            
        except Exception as e:
            self.logger.error(f"HWID Generation Failed: {e}")
            return "UNKNOWN_HWID"

    def generate_license_key(self, hwid: str) -> str:
        """
        Generates the Activation Key for a given HWID.
        (Included here for Keygen script import, but compiled inside Client logic implies risk?
         No, Client needs to Verify, so Client needs logic to checking signature.
         Actually simpler: Client calculates Signature(HWID). 
         If Client has Signature(HWID) stored, and it matches calculated Signature(CurrentHWID), then good.
         Wait, no. The Activation Key IS the Signature provided by Admin.
         
         Verification Logic:
         1. Client Calc: Expected_Key = HMAC(Current_HWID, Secret)
         2. User Input: User_Key
         3. Check: User_Key == Expected_Key
         
         So 'generate_license_key' logic MUST be present in Client to calculate Expected Key.
         As long as SECRET is hidden (via Cython), User cannot generate their own keys.
        """
        try:
            # HMAC-SHA256
            signature = hmac.new(self._SECRET, hwid.encode(), hashlib.sha256).hexdigest().upper()
            # Format: AAAA-BBBB-CCCC-DDDD
            return f"{signature[:4]}-{signature[4:8]}-{signature[8:12]}-{signature[12:16]}"
        except Exception:
            return ""

    def load_license(self) -> str:
        """Reads local license file"""
        if os.path.exists(self.LICENSE_FILE):
            try:
                with open(self.LICENSE_FILE, 'r') as f:
                    return f.read().strip()
            except:
                pass
        return ""

    def save_license(self, key: str):
        """Saves license to local file"""
        with open(self.LICENSE_FILE, 'w') as f:
            f.write(key.strip())

    def validate_license(self, key: str) -> bool:
        """
        Verifies if the provided key matches the expected HMAC for this machine.
        """
        if not key or len(key) < 10:
            return False
            
        current_hwid = self.get_hwid()
        expected_key = self.generate_license_key(current_hwid)
        
        # Constant time comparison to prevent timing attacks (overkill here but good practice)
        return hmac.compare_digest(key, expected_key)

