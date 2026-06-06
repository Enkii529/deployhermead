"""
Best Heroes Lead Generator
Fetches business leads for a location/industry using Hermes web_search.
Extracts phone, email, and best‑effort owner name from snippets.
"""

import argparse
import re
import sys

# When running inside Hermes execute_code we can import hermes_tools
try:
    from hermes_tools import web_search
except ImportError:
    print("Error: hermes_tools not available. Run this script via Hermes execute_code or within the agent context.", file=sys.stderr)
    sys.exit(1)

# Simple domain blacklist to avoid generic directories (unless you want them)
BLACKLIST_DOMAINS = {
    'wikipedia.org', 'yelp.com', 'facebook.com', 'instagram.com',
    'twitter.com', 'linkedin.com', 'tripadvisor.com', 'google.com',
    'bing.com', 'yellowpages.com', 'manta.com', 'ezlocal.com'
}

def is_blacklisted(url):
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower()
    return any(b in domain for b in BLACKLIST_DOMAINS)

PHONE_PATTERN = re.compile(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})')
EMAIL_PATTERN = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
# Owner patterns: look for "Owner: Name", "Manager: Name", etc.
OWNER_PATTERNS = [
    re.compile(r'Owner\s*[:\-]?\s*([A-Za-z .\'-]+)', re.IGNORECASE),
    re.compile(r'Manager\s*[:\-]?\s*([A-Za-z .\'-]+)', re.IGNORECASE),
    re.compile(r'Contact\s*[:\-]?\s*([A-Za-z .\'-]+)', re.IGNORECASE),
    re.compile(r'Founder\s*[:\-]?\s*([A-Za-z .\'-]+)', re.IGNORECASE),
    re.compile(r'President\s*[:\-]?\s*([A-Za-z .\'-]+)', re.IGNORECASE),
]

def extract_phones(text):
    return list(set(PHONE_PATTERN.findall(text)))

def extract_emails(text):
    return list(set(EMAIL_PATTERN.findall(text)))

def extract_owner(text):
    for pat in OWNER_PATTERNS:
        m = pat.search(text)
        if m:
            name = m.group(1).strip()
            if len(name) > 2 and len(name) < 50:
                return name
    return ""

def clean_business_name(title):
    # Remove common suffixes from search titles
    suffixes = [
        " - Yelp", " - Wikipedia", " - Google Search", " | Facebook", " | Instagram",
        " - Yellow Pages", " - Manta", " - EZlocal", " - TripAdvisor", " - Official Website"
    ]
    name = title
    for s in suffixes:
        if s in name:
            name = name.split(s)[0]
    return name.strip()

def generate_leads(location, industry=None, limit=20):
    # Build query to encourage phone numbers in snippets
    if industry:
        query = f"{industry} {location} phone contact"
    else:
        query = f"businesses {location} phone contact"

    # Fetch enough results; we'll filter later
    raw = web_search(query=query, limit=limit * 2)
    results = raw.get('data', {}).get('web', [])

    leads = []
    seen = set()  # dedup by phone+name

    for item in results:
        title = item.get('title', '')
        url = item.get('url', '')
        snippet = item.get('description', '')

        name = clean_business_name(title)
        if not name:
            continue

        # Basic business validation: if URL is blacklisted, still consider because snippet may contain phone, but we won't deep-crawl
        phone_match = PHONE_PATTERN.search(snippet)
        phone = phone_match.group(0) if phone_match else ""
        emails = extract_emails(snippet)
        email = emails[0] if emails else ""
        owner = extract_owner(snippet)

        # Dedup key
        key = (name.lower(), phone.lower())
        if key in seen:
            continue
        seen.add(key)

        lead = {
            "Business": name,
            "Phone": phone,
            "Email": email,
            "Owner": owner,
            "SourceURL": url,
            "Snippet": snippet[:150]  # keep short for context
        }
        leads.append(lead)
        if len(leads) >= limit:
            break

    return leads

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--location', required=True, help='City/State or region')
    parser.add_argument('--industry', help='Optional industry/category (e.g., restaurant, contractor)')
    parser.add_argument('--limit', type=int, default=20, help='Maximum number of leads')
    args = parser.parse_args()

    leads = generate_leads(args.location, industry=args.industry, limit=args.limit)
    # Print markdown table
    print("| Business | Phone | Email | Owner |")
    print("|----------|-------|-------|-------|")
    for l in leads:
        biz = l['Business'].replace('|', '\\|')
        phone = l['Phone'].replace('|', '\\|')
        email = l['Email'].replace('|', '\\|')
        owner = l['Owner'].replace('|', '\\|')
        print(f"| {biz} | {phone} | {email} | {owner} |")

if __name__ == "__main__":
    main()