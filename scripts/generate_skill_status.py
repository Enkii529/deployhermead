#!/usr/bin/env python3
import os
import re
from datetime import datetime

SKILLS_DIR = os.path.expanduser('~/.hermes/skills')
OUTPUT_DIR = os.path.expanduser('~/hermes')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def parse_skill_md(filepath):
    """Extract name, description, category from SKILL.md frontmatter."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    # Split frontmatter (between --- lines)
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            # Parse key-value lines
            name = None
            description = None
            category = None
            for line in frontmatter.splitlines():
                line = line.strip()
                if line.startswith('name:'):
                    name = line.split(':', 1)[1].strip()
                elif line.startswith('description:'):
                    description = line.split(':', 1)[1].strip()
                elif line.startswith('category:'):
                    category = line.split(':', 1)[1].strip()
            return {
                'name': name or os.path.basename(os.path.dirname(filepath)),
                'description': description or '',
                'category': category or 'uncategorized'
            }
    # Fallback: derive name from directory
    return {
        'name': os.path.basename(os.path.dirname(filepath)),
        'description': '',
        'category': 'uncategorized'
    }

def gather_skills():
    skills = []
    for category in os.listdir(SKILLS_DIR):
        cat_path = os.path.join(SKILLS_DIR, category)
        if not os.path.isdir(cat_path):
            continue
        for skill_name in os.listdir(cat_path):
            skill_path = os.path.join(cat_path, skill_name, 'SKILL.md')
            if os.path.isfile(skill_path):
                info = parse_skill_md(skill_path)
                info['category'] = category
                skills.append(info)
    return skills

def generate_report(skills):
    date_str = datetime.now().strftime('%Y-%m-%d')
    out_path = os.path.join(OUTPUT_DIR, f'skills_status_{date_str}.md')
    # Group by category
    by_cat = {}
    for s in skills:
        by_cat.setdefault(s['category'], []).append(s)
    # Build markdown
    lines = [
        '# Skill Status Report',
        f'Generated: {date_str}',
        f'Total skills: {len(skills)}',
        '',
        '## Overview by Category'
    ]
    for cat in sorted(by_cat.keys()):
        lines.append(f'\n### {cat}')
        for s in sorted(by_cat[cat], key=lambda x: x['name']):
            desc = s['description'][:80] + ('...' if len(s['description']) > 80 else '')
            lines.append(f'- **{s["name"]}**: {desc}')
    # Add raw table
    lines.extend(['', '## Full Table', '| Category | Skill | Description |', '|----------|-------|-------------|'])
    for s in sorted(skills, key=lambda x: (x['category'], x['name'])):
        desc = s['description'].replace('|', '\\|')
        lines.append(f'| {s["category"]} | {s["name"]} | {desc} |')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'Report written to {out_path}')

if __name__ == '__main__':
    skills = gather_skills()
    generate_report(skills)
