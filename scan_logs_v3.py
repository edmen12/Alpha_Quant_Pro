
import os
from pathlib import Path

# Use default log path
log_path = Path("logs/AlphaQuant.log")
output_path = Path("scan_result_utf8.txt")

keywords = [
    "[AGENT DEBUG]", 
    "Signal: HOLD", 
    "WAIT_SIGNAL"
]

print(f"Scanning {log_path} for Agent Debugs...")

if log_path.exists():
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
        matches = []
        for line in lines:
            if any(k in line for k in keywords):
                matches.append(line.strip())
        
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(f"Found {len(matches)} matches. Showing last 30:\n")
        # Show more context
        for m in matches[-30:]:
            out.write(m + "\n")
    print("Done.")
else:
    print("Log not found")
