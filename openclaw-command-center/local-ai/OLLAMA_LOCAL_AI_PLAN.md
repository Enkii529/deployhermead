# OLLAMA_LOCAL_AI_PLAN.md

## Purpose

Ollama will be used as the local AI backend for apps, dashboards, n8n automations, scripts, and background helper tools.

OpenClaw will remain on OpenRouter free as the main reasoning/project-management provider for now.

## Current Ollama Endpoint

Ollama runs on the Windows host.

Ubuntu VM reaches Ollama through:

$OLLAMA_BASE_URL

## Current Models

- gemma4:e4b
  - First local quality-test model
  - Better for richer local responses
  - Slower response time

- ministral-3:8b
  - Local fallback model
  - Good candidate for general tasks

- qwen2.5:3b
  - Fast helper/watcher model
  - Better for lightweight automations

## Best Uses

### gemma4:e4b
- summaries
- planning drafts
- report generation
- dashboard explanations
- higher-quality local responses

### ministral-3:8b
- fallback assistant tasks
- app helper responses
- medium reasoning

### qwen2.5:3b
- fast tagging
- classification
- watcher tasks
- short JSON outputs
- simple automation decisions

## Rules

1. Do not make Ollama the OpenClaw default provider yet.
2. Use Ollama through API calls from apps, scripts, dashboards, and n8n.
3. Test each model by task type before assigning it.
4. Prefer qwen2.5:3b for fast/cheap background jobs.
5. Prefer gemma4:e4b when quality matters more than speed.
6. Keep all test prompts in local-ai/prompts.
7. Keep all local AI app work inside local-ai/apps.
