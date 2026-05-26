#!/usr/bin/env python3
"""
Brain Status Report generator.
Queries Command Center panel API and creates a daily status report.
Writes to ~/hermes/cron/output/ and also prints to stdout.
"""
import os
import sys
import json
import urllib.request
from datetime import datetime
from pathlib import Path

# Command Center API base
API_URL = "http://127.0.0.1:8787/api/status"
# Output directory
OUTPUT_DIR = os.path.expanduser("~/hermes/cron/output")
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

def fetch_status():
    try:
        with urllib.request.urlopen(API_URL, timeout=10) as resp:
            if resp.status == 200:
                data = json.load(resp)
                return data
            else:
                return {"error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"error": str(e)}

def format_report(data):
    timestamp = datetime.utcnow().isoformat() + "Z"
    lines = []
    lines.append(f"# Brain Status Report")
    lines.append(f"**Generated:** {timestamp}")
    lines.append("")
    
    if "error" in data:
        lines.append(f"**ERROR:** Could not fetch status: {data['error']}")
        return "\n".join(lines)

    # Command Center queues
    queues = data.get("command_center", {}).get("queues", {})
    lines.append("## Command Center Queues")
    lines.append(f"- Inbox: **{queues.get('inbox', 'N/A')}**")
    lines.append(f"- Working: **{queues.get('working', 'N/A')}**")
    lines.append(f"- Done: **{queues.get('done', 'N/A')}**")
    lines.append(f"- Failed: **{queues.get('failed', 'N/A')}**")
    lines.append("")

    # Librarian info
    librarian = data.get("librarian", {})
    counts = librarian.get("counts", {})
    manifest = librarian.get("manifest", {})
    log = librarian.get("latest_log", {})
    
    lines.append("## Librarian")
    lines.append(f"- ChatGPT files: **{counts.get('chatgpt_files', 'N/A')}**")
    lines.append(f"- Lyrics files: **{counts.get('lyrics_files', 'N/A')}**")
    lines.append(f"- Manifest mtime: {manifest.get('mtime', 'N/A')}")
    if log.get('tail'):
        lines.append("### Latest log tail:")
        lines.append("```")
        lines.append(log['tail'].strip())
        lines.append("```")
    lines.append("")
    
    # Health summary
    health = "OK"
    # Simple heuristic
    if any(v > 100 for v in queues.values() if isinstance(v, int)):
        health = "WARNING: High queue counts"
    lines.append(f"## Overall Health: {health}")
    lines.append("")
    lines.append("---")
    lines.append("*This report is auto-generated daily.*")
    
    return "\n".join(lines)

def main():
    data = fetch_status()
    report = format_report(data)
    
    # Write to daily file
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    out_path = os.path.join(OUTPUT_DIR, f"brain-status-{date_str}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    # Also print to stdout for cron logs
    print(report)
    
    # Success
    return 0

if __name__ == "__main__":
    sys.exit(main())