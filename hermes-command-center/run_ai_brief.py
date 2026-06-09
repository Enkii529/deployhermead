import os
import re
import sys
import time
from datetime import datetime
from hermes_tools import web_search, text_to_speech, send_message

# Configuration
OUTPUT_DIR = '/media/sf_ClawdbotShared/outputs/daily_briefings'

# Queries: (display_name, search_query, result_limit)
QUERIES = [
    ("General AI Headlines", "site:digg.com/ai", 15),
    ("Open Source Voice Cloning", "open source AI voice cloning tool", 5),
    ("Open Source Video Generation", "open source AI video generation", 5),
    ("Open Source Music Generation", "open source AI music generation", 5),
    ("New LLM Models", "new LLM model 2025", 8),
    ("Open Source LLM Models", "open source LLM model 2025", 8),
    ("OpenRouter New Models", "OpenRouter new models 2025", 5),
    ("Nvidia AI Models", "Nvidia AI models 2025", 5),
]

def fetch_stories(start):
    raw_results = {}
    for name, query, limit in QUERIES:
        try:
            result = web_search(query=query, limit=limit)
            stories = result.get('data', {}).get('web', [])
            raw_results[name] = stories
            print(f"Fetched {len(stories)} stories for {name}")
        except Exception as e:
            print(f"Error fetching {name}: {e}", file=sys.stderr)
            raw_results[name] = []
    return raw_results

def combine_categories(raw_results):
    creative = []
    for cat in ["Open Source Voice Cloning", "Open Source Video Generation", "Open Source Music Generation"]:
        creative.extend(raw_results.get(cat, []))
    cloud = []
    for cat in ["OpenRouter New Models", "Nvidia AI Models"]:
        cloud.extend(raw_results.get(cat, []))
    categories = {
        "General AI Headlines": raw_results.get("General AI Headlines", []),
        "Open Source Creative AI Tools": creative,
        "New LLM Models": raw_results.get("New LLM Models", []),
        "Open Source LLM Models": raw_results.get("Open Source LLM Models", []),
        "New Cloud Models": cloud,
    }
    return categories

def dedup_and_limit(categories):
    seen_urls = set()
    final = {}
    order = ["General AI Headlines", "Open Source Creative AI Tools", "New LLM Models", "Open Source LLM Models", "New Cloud Models"]
    limits = {
        "General AI Headlines": 12,
        "Open Source Creative AI Tools": 10,
        "New LLM Models": 6,
        "Open Source LLM Models": 6,
        "New Cloud Models": 6,
    }
    for cat in order:
        lst = []
        for story in categories[cat]:
            url = story.get('url')
            if url and url not in seen_urls:
                seen_urls.add(url)
                lst.append(story)
        limit = limits.get(cat, 6)
        final[cat] = lst[:limit]
    return final

def build_transcript(final_categories, date_str):
    lines = [f"Daily AI Briefing – {date_str}\n"]
    for cat, stories in final_categories.items():
        lines.append(f"\n{cat}:\n")
        for i, story in enumerate(stories, 1):
            title = story.get('title', 'No title')
            desc = story.get('description', '')
            desc = desc.replace('\n', ' ').strip()
            if len(desc) > 200:
                desc = desc[:197] + "..."
            lines.append(f"{i}. **{title}**")
            lines.append(f"• {desc}\n")
    return "\n".join(lines)

def strip_urls(text):
    return re.sub(r'https?://\S+', '', text)

def build_worksheet(final_cats, date_str):
    lines = [f"# Open Source AI Software Worksheet – {date_str}"]
    open_source_cats = ["Open Source Creative AI Tools", "Open Source LLM Models"]
    for cat in open_source_cats:
        if cat not in final_cats:
            continue
        lines.append(f"\n## {cat}")
        for i, story in enumerate(final_cats[cat], 1):
            title = story.get('title', 'No title')
            desc = story.get('description', '').replace('\n', ' ').strip()
            if len(desc) > 200:
                desc = desc[:197] + "..."
            url = story.get('url', '')
            lines.append(f"{i}. **{title}**")
            if desc:
                lines.append(f"   {desc}")
            if url:
                lines.append(f"   Read more: {url}")
            lines.append("")
    return "\n".join(lines)

def main():
    start = time.time()
    lock_path = os.path.join(OUTPUT_DIR, "ai_brief.lock")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if os.path.exists(lock_path):
        print(f"Lock file exists, another instance is running. Exiting.")
        sys.exit(1)
    with open(lock_path, 'w') as f:
        f.write(str(os.getpid()))
    try:
        print(f"Starting ai_brief generation", flush=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        print(f"Fetching stories", flush=True)
        raw = fetch_stories(start)
        print(f"Fetched stories, combining categories", flush=True)
        categories = combine_categories(raw)
        final_cats = dedup_and_limit(categories)
        total_stories = sum(len(stories) for stories in final_cats.values())
        if total_stories == 0:
            print(f"No stories found.", flush=True)
            print("SILENT")
            sys.exit(0)
        print(f"Building transcript and worksheet", flush=True)
        transcript = build_transcript(final_cats, date_str)
        transcript_path = os.path.join(OUTPUT_DIR, f"transcript_{date_str}.md")
        with open(transcript_path, 'w') as f:
            f.write(transcript)
        worksheet_content = build_worksheet(final_cats, date_str)
        worksheet_path = os.path.join(OUTPUT_DIR, f"worksheet_{date_str}.md")
        with open(worksheet_path, 'w') as f:
            f.write(worksheet_content)
        print(f"Preparing audio text", flush=True)
        audio_text = strip_urls(transcript)
        audio_txt_path = os.path.join(OUTPUT_DIR, f"audio_text_{date_str}.txt")
        with open(audio_txt_path, 'w') as f:
            f.write(audio_text)
        audio_path = os.path.join(OUTPUT_DIR, f"briefing_{date_str}.mp3")
        print(f"Generating audio with text_to_speech", flush=True)
        tts_result = text_to_speech(text=audio_text, output_path=audio_path)
        print(f"TTS result: {tts_result}")
        if not os.path.exists(audio_path):
            raise RuntimeError("text_to_speech failed to create audio file")
        print(f"Audio generated, sending to Telegram", flush=True)
        message = f"Daily AI Briefing for {date_str}.\n\nAudio briefing attached.\nWorksheet attached.\n\nMEDIA:{audio_path}\nMEDIA:{worksheet_path}"
        send_message(target='telegram', message=message)
        print(f"Success: transcript={transcript_path}, audio={audio_path}, worksheet={worksheet_path}", flush=True)
    finally:
        try:
            if os.path.exists(lock_path):
                os.remove(lock_path)
        except Exception as e:
            print(f"Error removing lock: {e}", file=sys.stderr)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        raise