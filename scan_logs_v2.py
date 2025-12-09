
import os
from pathlib import Path

log_path = Path("logs/AlphaQuant.log")
keywords = ["Insufficient data", "Computing V7 features", "Loaded Agent Module", "predict() called", "Signal:"]
output_path = Path("scan_result_utf8.txt")

print(f"Scanning {log_path}...")

if log_path.exists():
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
        matches = []
        for line in lines:
            if any(k in line for k in keywords):
                matches.append(line.strip())
        
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(f"Found {len(matches)} matches. Showing last 20:\n")
        for m in matches[-20:]:
            out.write(m + "\n")
    print("Done.")
else:
    print("Log not found")
