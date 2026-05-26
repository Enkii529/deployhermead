#!/usr/bin/env python3
import json
import datetime
import re
import os
from pathlib import Path

date_str = datetime.date.today().strftime("%Y-%m-%d")
base_dir = Path(os.path.expanduser("~/hermes-command-center/daily_briefings"))

# Data embedded from search results
general = [
    {"title": "Digg - AI news, before it trends", "url": "https://digg.com/ai", "description": "3 days ago - See what's next in AI before it trends. Digg watches the people who move first."},
    {"title": "Digg", "url": "https://digg.com/ai/5kr8v2uo?rank=3", "description": "3 days ago - This also connects to the success of methods like GEPA: richer feedback representations, whether vector-valued or semantic/natural-language, can carry much more optimization signal than sparse scalar rewards. More broadly, we may need to rethink “reward” as a structured feedback object rather than a single compressed scalar."},
    {"title": "Top AI Papers This Week Spotlight Agents And Memory Models · Digg", "url": "https://digg.com/ai/01ayi6fs", "description": "2 days ago - Positive users are excited by recent AI papers spotlighting agent infrastructure like harnesses, memory models, and metacognition because the field appears to be converging on coordinated agent architectures."},
    {"title": "Hugging Face releases Carbon, a family of open autoregressive genomic foundation models in 500M, 3B, and 8B sizes that match Evo2-7B performance at 250 times higher throughput · Digg", "url": "https://digg.com/ai/e82rjbxc", "description": "4 days ago - Hugging Face releases open genomic models (500M, 3B, 8B) matching Evo2-7B at 250x higher throughput, emphasizing open, local, transparent AI for biology applications."},
    {"title": "A study finds frontier language models in agent setups outperform human reviewers on identifying accurate issues in 82 Nature-family papers per 45 expert scientists · Digg", "url": "https://digg.com/ai/rgq7ve3c", "description": "4 days ago - A study shows frontier LMs in agent harnesses outperform human reviewers on identifying issues in Nature papers, with 45 expert scientists validating the AI's superior performance."},
    {"title": "GitHub stars · Digg", "url": "https://digg.com/ai/github/stars", "description": "1 week ago - It adds domain-specific rendering of Pareto frontiers, prompt diffs, per-example valset rings, and reflection minibatches. Hermes Agent is a Python self-improving AI agent with a TUI."},
    {"title": "HashiCorp co-founder Mitchell Hashimoto warns of AI psychosis · Digg", "url": "https://digg.com/ai/ns3ww0vf", "description": "1 week ago - Mitchell Hashimoto warns companies suffer from AI psychosis, blocking rational talks on limitations and risks; rapid AI agent automation can produce globally incomprehensible systems."},
    {"title": "GBrain Adopts ZeroEntropy As Default Embedding And Reranking Option · Digg", "url": "https://digg.com/ai/o7o4hn4g", "description": "1 week ago - GBrain adopts ZeroEntropy as default embedding and reranker, praised for strong speed, cost, and benchmark upgrades over previous tools for personal AI scenarios."},
    {"title": "Subbarao Kambhampati, an ASU AI professor, flags ICML 2026 registration showing 'Sold Out' during the early bird window · Digg", "url": "https://digg.com/ai/t6v80uzj", "description": "1 day ago - ICML 2026 registration sold out during early bird window, reflecting high demand for premier AI conference."},
    {"title": "Anthropic Claude recovers access to 2015 Bitcoin wallet · Digg", "url": "https://digg.com/ai/29cfva0z", "description": "2 weeks ago - Anthropic's Claude AI recovered access to a Bitcoin wallet holding 5 BTC locked since 2015 by analyzing uploaded files from an old college computer."},
    {"title": "OpenAI's Jason Liu shares a draft GitHub post outlining methods to maximize Codex use by shifting from coding to broader knowledge work · Digg", "url": "https://digg.com/ai/ij7tiz5b", "description": "1 week ago - OpenAI's Jason Liu shares methods to maximize Codex by shifting from pure coding to broader knowledge work, sparking community discussion."},
    {"title": "AI Rankings · Digg", "url": "https://digg.com/ai/x/rankings", "description": "People actively involved in AI across research, startups, investing, engineering, and media, ranked from the X social graph."},
    {"title": "A Stanford PhD student's study finds 11 major AI models endorsed lying or illegal actions 47 percent of time · Digg", "url": "https://digg.com/ai/kk6j3hdh", "description": "6 days ago - A Stanford study finds AI models endorse lying or illegal actions 47% of the time, raising safety concerns."},
    {"title": "Greg Isenberg forecasts AI agents within 12 months · Digg", "url": "https://digg.com/ai/s2vsqi99", "description": "May 16, 2026 - Greg Isenberg predicts AI agents capable of performing jobs within 12 months, highlighting Hermes agents that write to memory after every task."},
    {"title": "NSF Launches $1.5B X-Labs Initiative For Next-Gen Scientific Instruments · Digg", "url": "https://digg.com/ai/ef26kqe2", "description": "4 days ago - NSF launches $1.5B X-Labs initiative to develop next-generation scientific instruments, boosting AI-driven research infrastructure."},
    {"title": "Zai_org Launches GLM-5.1-HighSpeed Achieving 400 Tokens Per Second · Digg", "url": "https://digg.com/ai/pawtqb5i", "description": "4 days ago - Zai_org launches GLM-5.1-HighSpeed achieving 400 tokens per second, showcasing rapid inference capabilities."},
    {"title": "Dan Hendrycks and William MacAskill release Eigenism framework paper · Digg", "url": "https://digg.com/ai/g37es8i7", "description": "2 weeks ago - Dan Hendrycks and William MacAskill release Eigenism framework paper, arguing superintelligent AIs may not retain human-like values."},
    {"title": "Live Music Diffusion Models Turn Offline Audio AI Into Real-Time Instruments · Digg", "url": "https://digg.com/ai/y3dn8o7m", "description": "3 days ago - Live music diffusion models enable offline audio AI to function as real-time instruments, expanding creative applications."},
    {"title": "This Week in AI Episode 14 roundtable with Imbue CEO on GPU investments and open source agents · Digg", "url": "https://digg.com/ai/n8ifljhu", "description": "3 days ago - This Week in AI hosts a roundtable with Imbue CEO Kanjun Qiu discussing early GPU cluster investments and open source agents."},
    {"title": "Velobase Open-Sources AI SaaS Framework To Drive Revenue Infrastructure · Digg", "url": "https://digg.com/ai/cyjpp832", "description": "5 days ago - Velobase open-sources its AI SaaS framework, emphasizing that infrastructure—not product—is the moat for converting users into revenue."},
    {"title": "AI-generated parody video depicts Andrej Karpathy joining Anthropic · Digg", "url": "https://digg.com/ai/x3d7xan9", "description": "1 day ago - AI-generated parody video humorously depicts Andrej Karpathy joining Anthropic, sparking mixed reactions about AI comedy capabilities."},
    {"title": "Google CEO Sundar Pichai Discusses AI Race, Backlash, and AGI · Digg", "url": "https://digg.com/ai/r4a7vl7n", "description": "3 days ago - Google CEO Sundar Pichai discusses the AI race, backlash, and whether he's AGI-pilled on the Hard Fork podcast, covering Google Search and AI usage."},
    {"title": "Google's AI Overview responds to single-word verb queries in unexpected ways · Digg", "url": "https://digg.com/ai/4q9z788z", "description": "Pattern: Google AI Overview responds oddly to single-word verb queries, as reported in multiple X posts and TechCrunch."},
    {"title": "Trump indicates he will postpone an executive order on AI after determining certain aspects · Digg", "url": "https://digg.com/ai/iic3mjom", "description": "Trump indicates postponement of an AI executive order pending further review, as US AI lead shows economic gains and job growth."},
    {"title": "Charts show sharp post-ChatGPT rises in creative and scientific output with weeks-long spillovers · Digg", "url": "https://digg.com/ai/anf0uyq7", "description": "Charts reveal significant increases in creative and scientific output following ChatGPT's release, with effects lasting weeks."},
    {"title": "Meta laid off 8,000 employees including high-performing engineers as AI tools do their jobs · Digg", "url": "https://digg.com/ai/apc3g2o3", "description": "Meta laid off 8,000 employees, including high-performing engineers, as AI tools take over their responsibilities, expected to spawn new startups."},
    {"title": "Jeff Bezos says artificial intelligence will elevate people and Linked efficiency gains to potential deflationary effects · Digg", "url": "https://digg.com/ai/lncy45l3", "description": "Jeff Bezos says AI will elevate people, linking efficiency gains to deflationary effects and cautioning against early regulation."},
    {"title": "Sundar Pichai discusses the accelerating race to AGI, AI costs dropping, and Google's preference for fast, affordable models · Digg", "url": "https://digg.com/ai/rq5xhbay", "description": "Sundar Pichai discusses the accelerating race to AGI, falling AI costs, and Google's focus on fast, affordable models."},
    {"title": "AI Automation Drives Human Hiring Surge At Every From 4 To 30 · Digg", "url": "https://digg.com/ai/knnl3u8c", "description": "AI automation paradoxically drives a human hiring surge across companies of all sizes from 4 to 30 employees."},
    {"title": "Mustafa Suleyman, Microsoft AI CEO, predicts AI will reach human-level cognitive abilities by 2030 · Digg", "url": "https://digg.com/ai/8l179a2k", "description": "May 17, 2026 - Microsoft AI CEO Mustafa Suleyman predicts AI will achieve human-level cognitive abilities by 2030, per Fortune."}
]

creative = [
    {"title": "GitHub - jamiepine/voicebox: The open-source AI voice studio", "url": "https://github.com/jamiepine/voicebox", "description": "Voicebox is a local-first AI voice studio offering free voice cloning and preset voices via Kokoro and Qwen CustomVoice, as an open-source alternative to ElevenLabs."},
    {"title": "Chatterbox: Open Source Text-to-Speech | Resemble AI", "url": "https://www.resemble.ai/learn/models/chatterbox", "description": "Chatterbox is Resemble AI's MIT-licensed open-source TTS model with emotion control, real-time generation, and zero-shot voice cloning from 5 seconds of audio."},
    {"title": "RVC Web UI - FREE, Open Source AI Voice Cloning", "url": "https://www.youtube.com/watch?v=g4td-n8-QZk", "description": "RVC WebUI provides unlimited, free voice conversion software that runs locally on your PC."},
    {"title": "Applio - AI Audio Tool", "url": "https://topai.tools/t/applio", "description": "Applio is an open-source AI voice cloning tool with over 26,000 voice models, offered as a desktop application for developers and businesses."},
    {"title": "KikiVoice - Free AI Voice Cloning Online", "url": "https://kikivoice.ai/ai-voice-cloning", "description": "KikiVoice offers free AI voice cloning with 75+ languages, accents, and emotion control, no sign-up required."},
    {"title": "GitHub - hpcaitech/Open-Sora: Democratizing Efficient Video Production", "url": "https://github.com/hpcaitech/Open-Sora", "description": "Open-Sora is an open-source AI video generation project aiming to democratize efficient video production; also see their commercial product Video Ocean."},
    {"title": "Mochi 1: AI Video Generator", "url": "https://mochi1ai.com/", "description": "Mochi 1 generates smooth, realistic motion at 30fps with exceptional textual prompt alignment for precise video creation."},
    {"title": "LTX-2 Model Open Source: AI Video Generator", "url": "https://ltx.io/model/open-source", "description": "LTX-2 is an open-source AI video generation model designed for research, education, and experimentation, released March 7, 2026."},
    {"title": "Genmo: Open video generation models", "url": "https://www.genmo.ai/", "description": "Genmo offers Mochi 1, a cutting-edge open-source text-to-video model that can be run locally, customized, or contributed to."},
    {"title": "Best Open Source AI Video Generation Models in 2026", "url": "https://www.pixazo.ai/blog/best-open-source-ai-video-generation-models", "description": "Overview of open-source video generation models, including compatibility with Diffusers and ComfyUI."},
    {"title": "Best Open Source AI Music Generators 2026", "url": "https://sourceforge.net/directory/ai-music-generators/", "description": "Directory for filtering open source AI music generators by OS, license, language, and project status."},
    {"title": "SOUNDRAW | AI Music Generator – Royalty Free Beats", "url": "https://soundraw.io/", "description": "SOUNDRAW is an AI music generator built by musicians to make music creation easy and accessible to everyone."},
    {"title": "Meta publishes music generation AI model as open source", "url": "https://gigazine.net/gsc_news/en/20230612-audiocraft-music-gen/", "description": "Meta's Audiocraft music generation AI model is open-sourced, enabling anyone to create high-quality music with text and voice input."}
]

new_llm = [
    {"title": "Google launches new AI models and brings 'thinking' to Gemini", "url": "https://techcrunch.com/2025/02/05/google-launches-new-ai-ms-and-brings-thinking-to-gemini/", "description": "Google launched Gemini 2.0 Pro Experimental and Gemini 2.0 Flash Thinking, bringing reasoning capabilities to the Gemini app."},
    {"title": "China's DeepSeek R1: Advanced LLM for reasoning-intensive tasks", "url": "https://www.businesstoday.in/technology/news/story/chinas-new-ai-model-that-rivals-openai-google-microsoft-is-taking-the-internet-by-storm-heres-why-462079-2025-01-27", "description": "DeepSeek R1 is an advanced Chinese LLM designed for reasoning-intensive tasks like mathematics and coding, challenging existing giants."},
    {"title": "Deep Dive into LLMs like ChatGPT", "url": "https://www.youtube.com/watch?v=7xTGNNLPyMI", "description": "YouTube deep dive into Large Language Model technology that powers ChatGPT and similar products for a general audience."},
    {"title": "LLM Leaderboard 2026: Compare 300+ Top AI Models", "url": "https://llm-stats.com/", "description": "Independent LLM leaderboard ranking GPT, Claude, Llama, DeepSeek and 300+ models by intelligence, speed, and price with continuous updates."},
    {"title": "Top 6 Chinese AI Models Like DeepSeek in 2026", "url": "https://www.index.dev/blog/chinese-ai-models", "description": "Chinese LLM landscape includes DeepSeek-V3 and Qwen3-Max (Alibaba's flagship, available since September 2025) with advanced architecture for efficiency and performance."}
]

open_source_llm = [
    {"title": "Mistral AI - Wikipedia", "url": "https://en.wikipedia.org/wiki/Mistral_AI", "description": "Mistral AI, founded in 2023, offers open-weight LLMs with a valuation over $14B as of 2025, blending open-source and proprietary models."},
    {"title": "Top Open-Source LLMs to Watch in Early 2025", "url": "https://datawizz.ai/blog/top-5-open-source-llms-3b-8b-parameters-to-watch-in-early-2025", "description": "Five open-source LLMs (3B-8B parameters) stand out for enterprises, developers, and researchers, led by Llama 3.2-8B Instruct as the most versatile."},
    {"title": "OpenAI launches open-source LLM GPT-OSS-120B", "url": "https://fortune.com/2025/08/05/openai-launches-open-source-llm-ai-model-gpt-oss-120b-deepseek/", "description": "OpenAI enters the open-source race with GPT-OSS-120B, following the industry shift triggered by DeepSeek R1's reasoning capabilities at lower cost."},
    {"title": "Running an open-source LLM in 2025", "url": "https://blog.mozilla.ai/running-an-open-source-llm-in-2025/", "description": "Open-source LLMs offer transparency and control; organizations pivot toward fully-open datasets and model weights for deeper customization and security."},
    {"title": "Best Open-Source LLM Models in 2026: Coding, Local, Agentic AI", "url": "https://huggingface.co/blog/daya-shankar/open-source-llms", "description": "Best open-source LLMs for agentic AI, which can plan, call tools, read/write files, and perform multi-step tasks beyond simple prompting."}
]

cloud = [
    {"title": "LLM Rankings | OpenRouter", "url": "https://openrouter.ai/rankings", "description": "OpenRouter provides LLM rankings and AI leaderboard based on benchmarks and real usage data from millions of developers."},
    {"title": "OpenRouter Free Models: All 28 Listed (May 2026)", "url": "https://costgoat.com/pricing/openrouter-free-models", "description": "OpenRouter offers 28 free AI models with zero cost and no credit card, varying in context length, capabilities, and rate limits."},
    {"title": "Top Open-source Models On OpenRouter In 2025", "url": "https://officechai.com/ai/these-were-the-top-open-source-models-on-openrouter-in-2025/", "description": "2025 saw a transformed open-source AI landscape on OpenRouter with diversified model families gaining market share beyond previous dominant players."},
    {"title": "OpenRouter Rankings April 2026: Top AI Models by Data", "url": "https://www.digitalapplied.com/blog/openrouter-rankings-april-2026-top-ai-models-data", "description": "April 2026 OpenRouter analysis shows MiMo-V2-Pro leading with 4.65T tokens, Xiaomi 22.3% market share, and Qwen 3.6 Plus in top 5."},
    {"title": "OpenRouter Review 2026: One API to Rule Them All?", "url": "https://deepreviewai.com/reviews/2026-02-05_openrouter-review/", "description": "OpenRouter acts as a gateway providing access to 300+ models from dozens of providers with OpenAI SDK compatibility, automatic fallbacks, and consolidated billing."},
    {"title": "NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4", "url": "https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4", "description": "NVIDIA's Nemotron-3 Nano 30B model is optimized for GPU-accelerated systems, leveraging CUDA for faster training and inference."},
    {"title": "AI Models | NVIDIA Developer", "url": "https://developer.nvidia.com/ai-models", "description": "NVIDIA Developer portal showcases AI models optimized for NVIDIA GPU infrastructure, accelerated by NVIDIA's inference platform."},
    {"title": "LLM Leaderboard - Comparison of over 100 AI models", "url": "https://artificialanalysis.ai/leaderboards/models", "description": "Artificial Analysis leaderboard compares 100+ AI models on intelligence, price, performance, speed (tokens/sec, latency), and context window."},
    {"title": "Free NVIDIA AI API Tutorial with GLM 4.7", "url": "https://www.youtube.com/watch?v=Pe1E2-Vk1Ao", "description": "Tutorial on using NVIDIA's Free AI API to access powerful models like GLM 4.7 and build AI applications using Python."},
    {"title": "NVIDIA NIM Free API (2026): Models & Guide", "url": "https://free-llm.com/provider/nvidia-nim", "description": "NVIDIA NIM offers developer-friendly API, comprehensive documentation, and quick integration of AI capabilities into applications with multiple model options."}
]

def normalize_url(url):
    if 'digg.com/ai/' in url and '?' in url:
        return url.split('?')[0]
    return url

seen = set()
def dedup_category(category_list):
    result = []
    for story in category_list:
        norm = normalize_url(story['url'])
        if norm not in seen:
            seen.add(norm)
            result.append(story)
    return result

general_dedup = dedup_category(general)
creative_dedup = dedup_category(creative)
new_llm_dedup = dedup_category(new_llm)
open_source_llm_dedup = dedup_category(open_source_llm)
cloud_dedup = dedup_category(cloud)

general_final = general_dedup[:12]
creative_final = creative_dedup[:8]
new_llm_final = new_llm_dedup[:5]
open_source_llm_final = open_source_llm_dedup[:5]
cloud_final = cloud_dedup[:5]

def create_bullet(story):
    title = story['title']
    desc = story['description']
    bullet = f"{title} – {desc}"
    # Remove timestamps like "3 days ago - ", "1 week ago - "
    bullet = re.sub(r'\b\d+ (day|week|month)s? ago - ', '', bullet)
    bullet = re.sub(r'\b(May|January|February|March|April|June|July|August|September|October|November|December) \d{1,2},? \d{4} - ', '', bullet)
    bullet = re.sub(r'\s+', ' ', bullet).strip()
    if len(bullet) > 200:
        bullet = bullet[:197] + '...'
    return bullet

for story in general_final:
    story['bullet'] = create_bullet(story)
for story in creative_final:
    story['bullet'] = create_bullet(story)
for story in new_llm_final:
    story['bullet'] = create_bullet(story)
for story in open_source_llm_final:
    story['bullet'] = create_bullet(story)
for story in cloud_final:
    story['bullet'] = create_bullet(story)

final_data = {
    "general": general_final,
    "creative": creative_final,
    "new_llm": new_llm_final,
    "open_source_llm": open_source_llm_final,
    "cloud": cloud_final
}

json_path = base_dir / f"final_categories_{date_str}.json"
with open(json_path, 'w') as f:
    json.dump(final_data, f, indent=2)

print(f"Wrote {json_path}")
total_stories = sum(len(v) for v in final_data.values())
print(f"Total stories: {total_stories}")
