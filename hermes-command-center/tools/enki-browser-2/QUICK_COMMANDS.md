# Quick Commands for Enki Browser 2

These are the simplest ways to interact with Enki Browser 2 from the command line using the wrapper script.

## Basic Health & Policy
```bash
cd /home/openclaw/openclaw-command-center/tools/enki-browser-2
./enki health      # Check if service is running
./enki policy      # View open-mode and domain stats
```

## Navigation & Content
```bash
./enki open https://example.com   # Navigate to a URL
./enki text                       # Extract visible text from current page
./enki dom                        # Get DOM summary
./enki content                     # Get full page HTML (POST)
```

## Screenshots & Runs
```bash
./enki screenshot                  # Capture and save screenshot to run folder
./enki runs                       # List all run folders
./enki inspect-run <runId>        # Inspect a specific run's artifacts
./enki run https://example.com   # Structured run (navigate + screenshot + text + dom)
```

## Interactive Actions
```bash
./enki click "a"                  # Click an element by CSS selector
./enki fill "input[name=q]" "value"  # Fill an input field
./enki press "Enter"              # Press a key on the page
```

## Diagnostics
```bash
./enki console                    # Get captured console messages
./enki network                    # Get failed network requests
```

## Overriding the Base URL
If the service is running on a different host/port, override the default:
```bash
ENKI_BROWSER_URL=http://127.0.0.1:4318 ./enki health
```

## Typical Workflow
```bash
cd /home/openclaw/openclaw-command-center/tools/enki-browser-2
./enki health                         # Ensure service is up
./enki open https://example.com      # Navigate
./enki screenshot                     # Capture screenshot
./enki text                          # Get visible text
./enki runs                          # Check run folders
LATEST=$(./enki runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runs"][-1])')
./enki inspect-run "$LATEST"          # Inspect latest run
```
