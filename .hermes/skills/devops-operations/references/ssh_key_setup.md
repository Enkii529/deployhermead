# SSH Setup for Windows Access

The Hermes VM needs to SSH into the Windows host to manage the Brain Docker stack.

- Windows username: `Jason`
- Private key location on VM: `~/.ssh/enkii_windows_ed25519`
- Test script: `/media/sf_ClawdbotShared/Brain/scripts/test_vm_to_windows_ssh.sh`
  Usage: `./test_vm_to_windows_ssh.sh 192.168.56.1`
- If the key is missing, generate a new one:
  `ssh-keygen -t ed25519 -f ~/.ssh/enkii_windows_ed25519 -N ""`
- Install the public key on Windows:
  - On Windows, run PowerShell as Administrator:
    `powershell -ExecutionPolicy Bypass -File R:\codex\brain-stack\install_windows_authorized_key.ps1`
    (or manually append the public key to `C:\Users\Jason\.ssh\authorized_keys`)
- After setup, verify:
  `ssh -i ~/.ssh/enkii_windows_ed25519 Jason@192.168.56.1 "whoami && hostname"`
