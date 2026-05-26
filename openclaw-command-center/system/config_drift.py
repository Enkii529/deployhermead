#!/usr/bin/env python3
import os
import json
import hashlib
import difflib
import shutil
from datetime import datetime

# Configuration
WATCHED_FILES = [
    "/home/openclaw/.hermes/config.yaml",
    "/home/openclaw/.config/systemd/user/wiki.service",
    "/home/openclaw/.config/systemd/user/health-daemon.service",
]
BASELINE_DIR = "/media/sf_ClawdbotShared/Brain/config_baselines"
REPORT_PATH = "/media/sf_ClawdbotShared/Brain/config_drift_report.md"

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def safe_name_from_path(path):
    # Convert absolute path to a safe filename: replace / with _, strip leading _
    name = path.replace("/", "_")
    if name.startswith("_"):
        name = name[1:]
    return name

def compute_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def normalize_content(content):
    # Normalize line endings and strip trailing whitespace
    lines = content.splitlines()
    normalized = [line.rstrip() for line in lines]
    # Ensure trailing newline (common diff marker)
    if normalized and not normalized[-1] == "":
        normalized.append("")
    return "\n".join(normalized)

def load_baseline_hashes():
    hashes = {}
    index_path = os.path.join(BASELINE_DIR, "index.json")
    if os.path.exists(index_path):
        try:
            with open(index_path, "r") as f:
                data = json.load(f)
                hashes = data.get("hashes", {})
        except:
            pass
    return hashes

def save_baseline_hashes(hashes):
    index_path = os.path.join(BASELINE_DIR, "index.json")
    with open(index_path, "w") as f:
        json.dump({"hashes": hashes, "updated": datetime.now().isoformat()}, f, indent=2)

def main():
    ensure_dir(BASELINE_DIR)
    # Load index of baseline hashes
    baseline_hashes = load_baseline_hashes()
    changed_files = []
    report_lines = []

    for path in WATCHED_FILES:
        if not os.path.exists(path):
            report_lines.append(f"* Skipped {path}: not found")
            continue
        # Determine baseline file
        safe_name = safe_name_from_path(path)
        baseline_path = os.path.join(BASELINE_DIR, safe_name)
        current_hash = compute_hash(path)
        # If no baseline exists, take one now
        if not os.path.exists(baseline_path):
            shutil.copy2(path, baseline_path)
            baseline_hashes[path] = current_hash
            report_lines.append(f"* Baseline created for {path}")
            continue
        # Compare hash
        stored_hash = baseline_hashes.get(path)
        if stored_hash == current_hash:
            continue  # no change
        # Drift detected: generate diff
        with open(baseline_path, "r", encoding="utf-8", errors="replace") as f:
            baseline_content = f.read()
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            current_content = f.read()
        # Normalize and compare contents to see if only whitespace differences
        norm_baseline = normalize_content(baseline_content)
        norm_current = normalize_content(current_content)
        if norm_baseline == norm_current:
            # Only whitespace/last newline difference: auto-correct
            shutil.copyfile(baseline_path, path)
            report_lines.append(f"* Auto-corrected {path} (whitespace/normalization)")
            baseline_hashes[path] = current_hash  # update baseline to current
            continue
        # Otherwise, generate unified diff
        diff = difflib.unified_diff(
            baseline_content.splitlines(keepends=True),
            current_content.splitlines(keepends=True),
            fromfile=f"baseline_{safe_name}",
            tofile=f"current_{safe_name}",
            n=3
        )
        diff_text = "".join(diff)
        diff_file = os.path.join(BASELINE_DIR, f"diff_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(diff_file, "w") as f:
            f.write(diff_text)
        report_lines.append(f"* Drift detected in {path} (diff saved to {os.path.basename(diff_file)})")
        changed_files.append(path)
        # Do not update baseline for manual review

    # Update baseline index
    save_baseline_hashes(baseline_hashes)

    # Write report
    with open(REPORT_PATH, "w") as f:
        f.write(f"# Configuration Drift Report\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        f.write("## Summary\n")
        f.write(f"- Watched files: {len(WATCHED_FILES)}\n")
        f.write(f"- Changes detected: {len(changed_files)}\n\n")
        f.write("## Details\n")
        for line in report_lines:
            f.write(line + "\n")
    print(f"Config drift check complete. Report: {REPORT_PATH}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        raise
