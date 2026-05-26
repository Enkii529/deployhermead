import os, re
from datetime import datetime
from hermes_tools import web_search

OUTPUT_DIR = os.path.expanduser('~/hermes-command-center/daily_briefings')
date_str = datetime.now().strftime('%Y-%m-%d')

QUERIES = [
    ('Open Source Voice Cloning', 'open source AI voice cloning tool', 10),
    ('Open Source Video Generation', 'open source AI video generation', 10),
    ('Open Source Music Generation', 'open source AI music generation', 10),
    ('Open Source LLM Models', 'open source LLM model 2025', 10),
]

def fetch_stories():
    raw = {}
    for name, query, limit in QUERIES:
        res = web_search(query=query, limit=limit)
        stories = res.get('data', {}).get('web', [])
        raw[name] = stories
    return raw

def dedup_and_collect(raw):
    seen = set()
    items = []
    for cat_name, stories in raw.items():
        for s in stories:
            url = s.get('url')
            if url and url not in seen:
                seen.add(url)
                title = s.get('title', 'No title')
                desc = s.get('description', '').replace('\n', ' ').strip()
                items.append((cat_name, title, desc, url))
    return items

def build_md(items):
    lines = [f'# Open Source AI Software Worksheet – {date_str}']
    from collections import defaultdict
    by_cat = defaultdict(list)
    for cat, title, desc, url in items:
        by_cat[cat].append((title, desc, url))
    for cat in sorted(by_cat):
        lines.append(f'## {cat}')
        for i, (title, desc, url) in enumerate(by_cat[cat], 1):
            lines.append(f'{i}. **{title}**')
            lines.append(f'   {desc}')
            lines.append(f'   URL: {url}')
            lines.append('')
    return '\n'.join(lines)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    raw = fetch_stories()
    items = dedup_and_collect(raw)
    total = len(items)
    print(f'Fetched {total} unique open source items across {len(QUERIES)} categories.')
    if not items:
        print('[SILENT]')
        return
    md_content = build_md(items)
    out_path = os.path.join(OUTPUT_DIR, f'worksheet_{date_str}.md')
    with open(out_path, 'w') as f:
        f.write(md_content)
    print(f'Worksheet saved to {out_path}')

if __name__ == '__main__':
    main()