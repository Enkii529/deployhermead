---
name: best-heroes-lead-gen
description: Generate targeted business leads for My Biz Heroes using web search.
version: 0.1.0
author: Hermes Agent
license: MIT
category: productivity
tags: [lead-generation, business-development]
---

# Best Heroes Lead Generation Skill

This skill helps find potential local business clients for My Biz Heroes. It performs a web search for businesses in a specified location (and optional industry), extracts available contact information, and produces a markdown table with a tailored reason why each business is a good candidate based on My Biz Heroes' service offerings.

## Usage

Run the script in a Hermes `execute_code` context or via the Python interpreter within the Hermes virtualenv.

From within Hermes, you can execute:

```python
import sys
sys.path.append('/home/openclaw/.hermes/skills/best-heroes-lead-gen')
import lead_gen
leads = lead_gen.generate_leads(location='Rhode Island', limit=100)
# leads is a list of dicts; you can print or save as needed
```

Or use the command‑line interface (if run directly):

```bash
source /home/openclaw/.hermes/hermes-agent/venv/bin/activate
python /home/openclaw/.hermes/skills/best-heroes-lead-gen/lead_gen.py --location "Rhode Island" --limit 100 --output leads.md
```

### Arguments

- `--location` (required): Geographic area, e.g., "Rhode Island", "Providence, RI", "Boston, MA".
- `--limit` (optional): Maximum number of leads to return (default 10, max 100).
- `--industry` (optional): Specific industry to focus on (e.g., "restaurant", "contractor", "salon").
- `--output` (optional): Output file path (default leads.md).

## How It Works

1. Builds a search query like "local businesses in Rhode Island" or "restaurants in Providence".
2. Calls Hermes `web_search` to retrieve results.
3. For each result:
   - Extracts a phone number from the snippet (if present).
   - Infers the business category using keyword matching.
   - Assigns a reason specific to that category based on My Biz Heroes' service tiers (Presence, Visibility, Smart Business Systems).
4. Deduplicates by URL and limits to the requested number.
5. Outputs a markdown table: Business | Phone | Reason.

## Customization

You can edit `lead_gen.py` to adjust the keyword‑to‑industry mapping or the reason statements to better match your messaging.

## Dependencies

- Hermes agent environment with `hermes_tools.web_search`.
- Internet access for web search.