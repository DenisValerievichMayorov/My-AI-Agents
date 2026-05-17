# PLAN.md

## Objective
1. **Fix the Infinite Chat Loop:** Resolve the tennis-match loop of `"Принято. Ожидаю новых инструкций."` in `ai_chat_room.txt` between the Windows host and the Termux-Phone node by improving `agent_listener.py`.
2. **Diagnose and Fix Gemini CLI:** Check the status of `gemini` command line tool on the Windows host and ensure it executes successfully.
3. **Automate Remote Nodes Setup:** Connect via SSH from Windows to Termux (`100.87.207.25`) and Chromebook (`100.106.187.105`) to configure public keys, check services, and generate `Termux_Report.md` and `Chromebook_Report.md`.

## Context, Memory & Existing Tools
- **Global Memory & Rules:** Defined in `c:\Users\anton\GEMINI.md` and `.clinerules`.
- **GMC Configuration:** IP addresses, ports, and instructions are in `c:\Users\anton\Sync\GMC_Network_Control.md`.
- **SSH Private Key:** `c:\Users\anton\Sync\chromebook_ssh_key` is available.
- **Python Environment:** Windows host has `py` installed.

### Current Status (2026-05-17)
- **Diagnose Gemini CLI:** Completed. CLI is functional on Windows.
- **Fix agent_listener.py:** Improved with better de-duplication and stop-phrases.
- **Fix get_gmail.py loop:** Modified to search only for `UNSEEN` emails and updated `sensors.py` for better parsing.
- **Network Check:** SSH to Chromebook and Termux verified.
- **Cleanup ai_chat_room.txt:** Completed, sync conflicts removed.
- **Sync Automation:** Created `auto-sync.sh` on Chromebook and updated `INSTRUCTIONS_WINDOWS.md`.
- **Chromebook Report:** Updated with sync automation status.
- **OCR Werkraport:** Completed. Work schedule for Week 21 (May 18-24) extracted.

### Step 3: Cleanup `ai_chat_room.txt` [DONE]
- Remove the repetitive loops of duplicate messages from `ai_chat_room.txt`, keeping only the system events and the last relevant status.

### Step 4: Check SSH Connectivity to Remote Nodes [DONE]
- Test SSH connection to `Termux-Phone` (`100.87.207.25:8022`).
- Test SSH connection to `Chromebook` (`100.106.187.105:22` as `denisvalerievichmayorov1`).

### Step 5: Configure and Report Remote Nodes
- **Termux Phone:**
  - Verify tailscale status.
  - Setup SSH authorized keys using the public key.
  - Verify if `antigravity-cli` or similar service is installed/demoniized.
  - Write `Sync/Termux_Report.md` with status.
- **Chromebook:**
  - Verify `sshd` config on `tailscale0`.
  - Setup SSH authorized keys using `chromebook_ssh_key.pub`.
  - Check `rclone` Google Drive sync.
  - Write `Sync/Chromebook_Report.md`.

## Self-Healing Tools
- Run `py agent_listener.py` diagnostics locally and verify no syntax or runtime errors occur.
- Run tests on `sensors.py` and `heartbeat.py` to ensure their integrity.
