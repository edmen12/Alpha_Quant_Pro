
import subprocess
import time
import sys
import os
from datetime import datetime

TARGET_SCRIPT = "terminal_apple.py"
FROZEN_TARGET = "AlphaQuantPro.exe" 
COOLDOWN_SECONDS = 5

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [GUARDIAN] {msg}")

def main():
    log(f"Starting Guardian...")
    
    # Check if running as compiled executable
    if getattr(sys, 'frozen', False):
        # We are an exe. We assume the main app exe is next to us.
        base_dir = os.path.dirname(sys.executable)
        target_path = os.path.join(base_dir, FROZEN_TARGET)
        cmd = [target_path]
        target_display = FROZEN_TARGET
    else:
        # We are a script. Use current python to run the target script.
        cmd = [sys.executable, TARGET_SCRIPT]
        target_display = TARGET_SCRIPT


    log(f"Target: {target_display}")

    while True:
        try:
            log(f"🚀 Launching {target_display}...")
            # Run and wait
            process = subprocess.call(cmd)
            
            # Check exit code
            if process == 0:
                log("Application closed normally (Exit Code 0). Stopping Guardian.")
                break
            else:
                log(f"⚠️ Application crashed or closed unexpectedly (Exit Code {process}).")
                log(f"Restarting in {COOLDOWN_SECONDS} seconds...")
                time.sleep(COOLDOWN_SECONDS)
                
        except KeyboardInterrupt:
            log("🛑 Guardian stopped by user.")
            break
        except Exception as e:
            log(f"❌ Guardian Error: {e}")
            time.sleep(COOLDOWN_SECONDS)

if __name__ == "__main__":
    if not os.path.exists(TARGET_SCRIPT):
        print(f"Error: {TARGET_SCRIPT} not found!")
    else:
        main()
