#!/usr/bin/env python3
import json
import datetime
import re
from pathlib import Path

date_str = datetime.date.today().strftime("%Y-%m-%d")
base_dir = Path.home() / "hermes-command-center" / "daily_briefings"
json_path = base_dir / f"final_categories_{date_str}.json"

with open(json_path) as f:
    data = json.load(f)

category_order = ["general", "creative", "new_llm", "open_source_llm", "cloud"]
display_names = {
    "general": "General AI News",
    "creative": "Open Source Creative AI Tools",
    "new_llm": "New LLM Models",
    "open_source_llm": "Open Source LLM Models",
    "cloud": "New Cloud Models"
}

lines = [f"# AI Briefing Worksheet – {date_str}\n\n"]
for cat in category_order:
    if cat in data:
        lines.append(f"## {display_names.get(cat, cat)}\n")
        for i, story in enumerate(data[cat], 1):
            title = story['title']
            bullet = story.get('bullet', '')
            url = story['url']
            # Clean bullet: remove timestamps
            bullet_clean = re.sub(r'\b\d+ (day|week|month)s? ago - ', '', bullet)
            bullet_clean = re.sub(r'\b(May|January|February|March|April|June|July|August|September|October|November|December) \d{1,2},? \d{4} - ', '', bullet_clean)
            bullet_clean = re.sub(r'\s+', ' ', bullet_clean).strip()
            lines.append(f"{i}. **{title}**\n   {bullet_clean}\n   Link: {url}\n")
        lines.append("\n")

worksheet_path = base_dir / f"worksheet_{date_str}.md"
with open(worksheet_path, 'w') as f:
    f.writelines(lines)

print(f"Wrote {worksheet_path}")
