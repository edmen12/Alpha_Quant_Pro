
import os
from pathlib import Path

# Target console output
log_path = Path("console_output.txt")
output_path = Path("scan_console_result.txt")

keywords = [
    "[AGENT DEBUG]", 
    "Signal: BUY",
    "Signal: SELL",
    "Signal: HOLD", 
    "WAIT_SIGNAL",
    "P_BUY",
    "P_SELL",
    "H1_TREND",
    "[FE DEBUG]",
    "Config Loaded",
    "lot_size"
]

print(f"Scanning {log_path} for Agent Debugs...")

if log_path.exists():
    try:
        with open(log_path, "r", encoding="utf-16", errors="replace") as f:
            lines = f.readlines()
    except UnicodeError:
        # Fallback to utf-8 if not utf-16
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
