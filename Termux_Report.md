# Termux Report (2026-05-17)

## Status: ONLINE (via Tailscale)
- **IP Address:** `100.87.207.25`
- **Port:** `8022`
- **Tailscale Connection:** OK
- **SSH Connectivity:** TCP connection successful, but Authentication failed.

## Issues
- **SSH Authentication:** [ОЖИДАЕТ ИМПОРТА КЛЮЧА]. The public key `chromebook_ssh_key.pub` needs to be added to `~/.ssh/authorized_keys` on the Termux node.

## Actions Taken
- Verified connectivity from Windows host.
- Cleaned up `ai_chat_room.txt` loop.
- Identified security leak (OpenRouter API Key) in shared logs.

## Required Manual Step
To enable full automation on this node, please run the following command in Termux:
```bash
mkdir -p ~/.ssh && cat ~/Sync/chromebook_ssh_key.pub >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys
```
