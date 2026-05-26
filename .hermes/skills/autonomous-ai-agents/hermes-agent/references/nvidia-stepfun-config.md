# Nvidia + Stepfun Provider Config

## What works for Jason

**Provider:** Nvidia (integrate.api.nvidia.com)  
**Model:** `stepfun-ai/step-3.5-flash`  
**Auth:** Nvidia API key (`nvapi-...`) — stored in `providers.nvidia.api_key` in config.yaml

## Working config block

```yaml
model:
  default: stepfun-ai/step-3.5-flash
  provider: nvidia
  base_url: https://integrate.api.nvidia.com/v1
  api_mode: chat_completions
providers:
  nvidia:
    api_key: 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
```

## Key commands

```bash
# Verify config path
hermes config path

# Set model + provider in one shot
hermes config set model.default stepfun-ai/step-3.5-flash
hermes config set model.provider nvidia

# Add API key to provider
hermes config set providers.nvidia.api_key nvapi-...
```

## Gotcha

The `model.default` must also be updated when switching models — just setting `providers.nvidia.api_key` alone won't switch the active model.

## Restart required

Config changes to `model.*` or `providers.*` require a fresh session (`/reset` in gateway, or restart CLI).