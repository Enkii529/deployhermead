# Hermes Agent Deployment Guide

This guide explains how to restore your Hermes agent on a new VM using the backup repository `deployhermead`.

## Prerequisites

- Fresh Ubuntu (or compatible) VM with internet access.
- Git installed.
- SSH key added to your GitHub account with read access to the repo. (Clone via SSH.)
- The VM must later mount the shared Brain at `/media/sf_ClawdbotShared` if using the full system (Brain is backed up separately).

## Steps

1. **Get the repository**
   - **Clone**: `git clone git@github.com-deployhermead:Enkii529/deployhermead.git ~/hermes-agent-backup`
   - **Or download ZIP** and extract so `deploy.sh` sits at the folder root.

2. **Run the deployment script**
   ```bash
   cd ~/hermes-agent-backup
   chmod +x deploy.sh
   ./deploy.sh
   ```
   The script will:
   - Copy `hermes-command-center/`, `openclaw-command-center/`, `.hermes/`, and `scripts/` into your home directory.
   - Restore your saved crontab (from `config/user_crontab.txt`).
   - Create the daily briefings output directory.
   - Set appropriate permissions.

3. **Restart Hermes**
   - Systemd: `systemctl --user restart hermes`
   - Or simply reboot the VM.

4. **Mount the Brain** (if using it)
   - Ensure the shared folder `/media/sf_ClawdbotShared/Brain` is mounted. The Hermes config already points to the Brain API; once mounted, agents will function as a team.

5. **Verify**
   - Trigger a brief: `hermes --skill ai-brief`
   - Check `~/hermes-command-center/daily_briefings/` for outputs.

## Notes

- The deploy script is idempotent; running it multiple times is safe.
- The backup does **not** include Brain data (separate repo). Brain connection details are in `~/.hermes/config.yaml`.
- Large model files and caches are excluded to keep the repo small.
- To change paths or exclusions, edit `deploy.sh` and `.gitignore` before creating your next backup.

## Support

Issues? Consult Hermes docs or open an issue in the backup repository.