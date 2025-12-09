
import os
from pathlib import Path

log_path = Path("logs/AlphaQuant.log")
keywords = ["Insufficient data", "Computing V7 features", "Loaded Agent Module", "predict() called", "Signal:"]
print(f"Scanning {log_path}...")

if log_path.exists():
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
        # Print last 50 lines matching keywords
        matches = []
        for line in lines:
            if any(k in line for k in keywords):
                matches.append(line.strip())
        
        print(f"Found {len(matches)} matches. Showing last 20:")
        for m in matches[-20:]:
            print(m)
else:
    print("Log not found")
