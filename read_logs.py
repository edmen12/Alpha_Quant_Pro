
import os
from pathlib import Path

try:
    log_dir = Path(os.environ.get('LOCALAPPDATA', Path.home())) / "AlphaQuantPro" / "logs"
    log_path = log_dir / "debug_log.txt"
    print(f"Reading log from: {log_path}")
    
    if not log_path.exists():
        print("Log file not found.")
    else:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            print(f.read())
except Exception as e:
    print(f"Error: {e}")
