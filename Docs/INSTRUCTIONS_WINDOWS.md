# Instructions for Windows Node (Anton)
**Host:** DESKTOP-85D3NJI
**User:** anton

## 1. SSH Access to Remote Nodes
Use the following commands from PowerShell or CMD to access remote nodes via Tailscale:

### Access Chromebook:
```powershell
ssh -i c:\Users\anton\Sync\chromebook_ssh_key denisvalerievichmayorov1@100.106.187.105
```

### Access Termux (Phone):
```powershell
ssh -p 8022 100.87.207.25
```

## 2. Sync Configuration
- **Syncthing:** Ensure Syncthing is running and syncing `c:\Users\anton\Sync` with the remote nodes.
- **Rclone:** The Chromebook node now has an `auto-sync.sh` script that runs every 15 minutes to bisync with Google Drive (`gdrive:Sync`).

## 3. Gemini CLI on Windows
- Gemini CLI is functional. Use it to coordinate tasks between nodes.
- Any updates to `Sync/PLAN.md` will be picked up by other nodes.

## 4. Maintenance
- Check `Sync/heartbeat.log` for system health.
- Use `Sync/GMC_Network_Control.md` as the primary reference for IP addresses and network setup.
