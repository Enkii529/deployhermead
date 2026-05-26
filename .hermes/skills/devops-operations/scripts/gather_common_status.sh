#!/bin/bash
# Gather concise system status snapshot for operational reviews
echo "=== Hermes Gateway ==="
hermes gateway status 2>/dev/null || echo "hermes gateway status failed"
echo -e "\n=== Disk Usage (home) ==="
df -h /home/openclaw | tail -n1
echo -e "\n=== Key Processes (grep hermes) ==="
pgrep -f hermes -a | head -n 10
echo -e "\n=== Bot_Exchange Queues ==="
ls -l /media/sf_ClawdbotShared/Brain/Bot_Exchange/queue/
echo -e "\n=== Recent Gateway Log (tail) ==="
tail -n 20 ~/.hermes/logs/gateway.log 2>/dev/null | grep -E "WARNING|ERROR|INFO" || echo "Log not accessible"
echo -e "\n=== Docker (if any) ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "docker not available"
