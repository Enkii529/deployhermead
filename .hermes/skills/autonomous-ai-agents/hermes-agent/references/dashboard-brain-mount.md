# Dashboard Setup on Shared Brain Mount

When the Brain is stored on a shared VirtualBox folder (e.g., `/media/sf_ClawdbotShared/Brain`) and you want to run the Command Center Dashboard, the systemd user service must point to the correct location.

## Service file

Edit `~/.config/systemd/user/hermes-dashboard.service`:

```ini
[Unit]
Description=Hermes Command Center Dashboard
After=network.target

[Service]
Type=simple
WorkingDirectory=/media/sf_ClawdbotShared/Brain/command_center_panel
ExecStart=/usr/bin/python3 /media/sf_ClawdbotShared/Brain/command_center_panel/app.py
Restart=on-failure
RestartSec=10
Environment=PORT=8787

[Install]
WantedBy=default.target
```

Use `/usr/bin/python3` if you install Flask system-wide (`sudo apt install python3-flask`). Alternatively, use the Hermes virtualenv Python:

```
ExecStart=/home/openclaw/.hermes/hermes-agent/venv/bin/python /media/sf_ClawdbotShared/Brain/command_center_panel/app.py
```

If you use the venv, ensure Flask is installed inside it. The venv may lack `pip`; bootstrap it:

```bash
/home/openclaw/.hermes/hermes-agent/venv/bin/python -m ensurepip --upgrade
/home/openclaw/.hermes/hermes-agent/venv/bin/pip install flask==3.0.2
```

## Apply changes

After editing:

```bash
systemctl --user daemon-reload
systemctl --user start hermes-dashboard.service   # or restart
```

Check status:

```bash
systemctl --user status hermes-dashboard.service
```

The dashboard should be reachable at `http://localhost:8787`.