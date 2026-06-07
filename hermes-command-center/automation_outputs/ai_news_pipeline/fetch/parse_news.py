import re
import json
from datetime import datetime, timedelta, timezone
import sys

def parse_date(date_str):
    """Parse date string, handling ISO and relative dates."""
    date_str = date_str.strip()
    
    # Handle relative dates like "Opinion4 minutes ago" or "2 hours ago"
    if 'ago' in date_str.lower() or 'minute' in date_str.lower() or 'hour' in date_str.lower():
        # Treat as recent (now) - timezone aware
        return datetime.now(timezone.utc)
    
    # Handle "Opinion4 minutes ago" format
    if date_str.startswith('Opinion'):
        return datetime.now(timezone.utc)
    
    # Try ISO format
    try:
        # Handle timezone offset
        if 'T' in date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        pass
    
    # Default to now if unparseable - timezone aware
    return datetime.now(timezone.utc)

# Read the ddgs output from stdin
output = sys.stdin.read()

# Parse the output - each entry starts with a number followed by newline
# Fields: date, title, body, url, image, source
entries = []
current_entry = {}

lines = output.strip().split('\n')
i = 0
while i < len(lines):
    line = lines[i].strip()
    
    # Check if line starts with a number (entry delimiter)
    if re.match(r'^\d+\.$', line):
        if current_entry:
            entries.append(current_entry)
        current_entry = {}
        i += 1
        continue
    
    # Parse key-value pairs
    if line.startswith('date'):
        date_str = line[4:].strip()
        current_entry['date_raw'] = date_str
        current_entry['date_parsed'] = parse_date(date_str)
    elif line.startswith('title'):
        current_entry['title'] = line[5:].strip()
    elif line.startswith('body'):
        current_entry['body'] = line[4:].strip()
    elif line.startswith('url'):
        current_entry['url'] = line[3:].strip()
    elif line.startswith('source'):
        current_entry['source'] = line[6:].strip()
    elif line.startswith('image'):
        # skip image for now
        pass
    
    i += 1

# Don't forget the last entry
if current_entry:
    entries.append(current_entry)

# Filter to past 24h
now = datetime.now(timezone.utc)
cutoff = now - timedelta(hours=24)

filtered = []
for e in entries:
    if e.get('date_parsed') and e['date_parsed'] >= cutoff:
        filtered.append({
            'title': e.get('title', ''),
            'url': e.get('url', ''),
            'source': e.get('source', ''),
            'date': e.get('date_raw', ''),
            'body': e.get('body', '')
        })

# Sort by date descending (newest first)
filtered.sort(key=lambda x: x.get('date_parsed', datetime.min.replace(tzinfo=timezone.utc)), reverse=True)

# Take top 12
result = filtered[:12]

# Output JSON
print(json.dumps(result, indent=2))
