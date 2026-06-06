#!/usr/bin/env python3
"""
Brain Wiki Update Script
Generates static HTML pages from system data sources.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# Optional: import hermes_tools if available
try:
    from hermes_tools import session_search, read_file, search_files
    HERMES_TOOLS_AVAILABLE = True
except ImportError:
    HERMES_TOOLS_AVAILABLE = False

# Optional: import Jinja2
try:
    from jinja2 import Environment, FileSystemLoader
    JINJA_AVAILABLE = True
except ImportError:
    JINJA_AVAILABLE = False

# Configuration
WIKI_ROOT = Path('/media/sf_ClawdbotShared/Brain/wiki')
SCRIPTS_DIR = WIKI_ROOT / 'scripts'
DATA_DIR = WIKI_ROOT / 'data'
TEMPLATES_DIR = WIKI_ROOT / 'templates'
LOGS_DIR = WIKI_ROOT / 'logs'
STATIC_DIR = WIKI_ROOT / 'static'
LOG_FILE = LOGS_DIR / 'update.log'

def log(message, level='INFO'):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] [{level}] {message}\n")
    print(f"[{level}] {message}")

def load_json_file(path, default=None):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log(f"Error loading {path}: {e}", 'WARNING')
        return default if default is not None else []

def load_jsonlines_file(path, default=None):
    result = []
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        result.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        log(f"Error parsing JSONL line in {path}: {e}", 'WARNING')
        return result
    except FileNotFoundError:
        log(f"File {path} not found, using default", 'WARNING')
        return default if default is not None else []

def get_ports():
    path = DATA_DIR / 'app_ports.json'
    return load_json_file(path, [])

def get_ideas():
    path = DATA_DIR / 'ideas.jsonl'
    return load_jsonlines_file(path, [])

def get_trade_models():
    path = DATA_DIR / 'trade_models.jsonl'
    return load_jsonlines_file(path, [])

def get_manual_trades():
    path = DATA_DIR / 'manual_trades.jsonl'
    return load_jsonlines_file(path, [])

def get_skills_catalog():
    """Load skills from ~/hermes/skills/"""
    skills_dir = Path.home() / 'hermes' / 'skills'
    skills = []
    categories = set()

    if skills_dir.exists():
        for category_dir in skills_dir.iterdir():
            if category_dir.is_dir():
                skill_file = category_dir / 'SKILL.md'
                if skill_file.exists():
                    try:
                        with open(skill_file, 'r') as f:
                            content = f.read()
                            # Parse frontmatter (YAML between --- lines)
                            if content.startswith('---'):
                                parts = content.split('---', 2)
                                if len(parts) >= 3:
                                    frontmatter = parts[1].strip()
                                    body = parts[2].strip()
                                    # Simple extraction of name and description
                                    skill_data = {'category': category_dir.name, 'body': body}
                                    for line in frontmatter.split('\n'):
                                        if ':' in line:
                                            key, value = line.split(':', 1)
                                            skill_data[key.strip()] = value.strip().strip('"\'')
                                    skills.append(skill_data)
                                    categories.add(category_dir.name)
                    except Exception as e:
                        log(f"Error parsing {skill_file}: {e}", 'WARNING')

    return skills, list(categories)

def get_agent_roles():
    """Scan Brain for agent-related info."""
    brain_root = Path('/media/sf_ClawdbotShared/Brain')
    agents = []
    agents_summary = []

    # Look for agent config files
    if brain_root.exists():
        for pattern in ['**/agents/*.md', '**/agent*.yaml', '**/agent*.json']:
            for file_path in brain_root.glob(pattern):
                try:
                    agents.append(str(file_path.relative_to(brain_root)))
                except:
                    pass

        # Also search for agent info in command center
        cc_file = brain_root / 'DAILY_COMMAND_CENTER.md'
        if cc_file.exists():
            agents_summary.append("Hermes Agent (from command center)")

    return agents, agents_summary

def get_brain_changes(hours=24):
    """List recently modified files in Brain."""
    brain_root = Path('/media/sf_ClawdbotShared/Brain')
    changes = []
    cutoff = datetime.now() - timedelta(hours=hours)

    if brain_root.exists():
        for root, dirs, files in os.walk(brain_root):
            for file in files:
                path = Path(root) / file
                try:
                    mtime = datetime.fromtimestamp(path.stat().st_mtime)
                    if mtime > cutoff:
                        changes.append({
                            'path': str(path.relative_to(brain_root)),
                            'mtime': mtime.strftime('%Y-%m-%d %H:%M')
                        })
                except:
                    pass

    changes.sort(key=lambda x: x['mtime'], reverse=True)
    return changes[:20]  # Limit to 20 most recent

def get_recent_sessions(days=7):
    """Get recent sessions from session DB if hermes_tools available."""
    if not HERMES_TOOLS_AVAILABLE:
        return []

    try:
        # This would need proper implementation; placeholder
        return []  # For now, we'll skip complex session search
    except Exception as e:
        log(f"Error fetching sessions: {e}", 'WARNING')
        return []

def get_command_center_entries():
    """Extract recent entries from DAILY_COMMAND_CENTER.md."""
    cc_path = Path('/media/sf_ClawdbotShared/Brain/DAILY_COMMAND_CENTER.md')
    entries = []
    if cc_path.exists():
        try:
            with open(cc_path, 'r') as f:
                lines = f.readlines()
                # Get last 10 non-empty lines
                non_empty = [line.strip() for line in lines if line.strip()]
                for line in non_empty[-10:]:
                    entries.append({'timestamp': 'Recent', 'content': line})
        except Exception as e:
            log(f"Error reading command center: {e}", 'WARNING')
    return entries

def render_template(template_name, context):
    """Render an HTML template with given context."""
    if not JINJA_AVAILABLE:
        log("Jinja2 not available, skipping HTML generation", 'ERROR')
        return None

    try:
        env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
        template = env.get_template(template_name)
        return template.render(**context)
    except Exception as e:
        log(f"Error rendering {template_name}: {e}", 'ERROR')
        return None

def main():
    start_time = datetime.now()
    log("Starting wiki sync...")

    # Ensure directories exist
    for dir_path in [WIKI_ROOT, TEMPLATES_DIR, STATIC_DIR, LOGS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Gather data
    log("Collecting data...")
    ports = get_ports()
    ideas = get_ideas()
    trade_models = get_trade_models()
    manual_trades = get_manual_trades()
    skills, categories = get_skills_catalog()
    agents, agents_summary = get_agent_roles()
    brain_changes = get_brain_changes(24)
    sessions = get_recent_sessions(7)
    command_center = get_command_center_entries()

    # Build context
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    context = {
        'timestamp': timestamp,
        'ports': ports,
        'ideas': ideas,
        'trade_models': trade_models,
        'manual_trades': manual_trades,
        'skills': skills,
        'skills_count': len(skills),
        'categories_count': len(categories),
        'agents': agents,
        'agents_count': len(agents),
        'agents_summary': agents_summary,
        'brain_changes': brain_changes,
        'sessions': sessions,
        'command_center_entries': command_center,
    }

    # Render templates
    templates = ['index.html', 'log.html', 'portfolio.html', 'trades.html', 'instructions.html']
    pages_generated = 0

    for tmpl in templates:
        html = render_template(tmpl, context)
        if html is not None:
            output_path = WIKI_ROOT / tmpl
            with open(output_path, 'w') as f:
                f.write(html)
            pages_generated += 1
            log(f"Generated {tmpl}")

    # Summary
    elapsed = datetime.now() - start_time
    log(f"Wiki sync completed in {elapsed.total_seconds():.2f}s")
    log(f"Generated {pages_generated} pages")
    log(f"Skills: {len(skills)}, Categories: {len(categories)}, Agents: {len(agents)}")
    log(f"Brains changes: {len(brain_changes)}, Ideas: {len(ideas)}")

    print("Wiki sync completed successfully.")
    return 0

if __name__ == '__main__':
    exit(main())