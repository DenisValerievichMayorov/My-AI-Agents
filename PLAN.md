# PLAN.md

## Objective
Reorganize and clean up the `C:\Users\anton\Sync` folder structure to strictly adhere to the `SYNC_STRUCTURE.md` protocol:
1. **Consolidate `AGENTS_COMPLAINTS.md`:** Merge the massive root `AGENTS_COMPLAINTS.md` (294 KB), scripts folder `AGENTS_COMPLAINTS.md` (7.6 KB), and log folder `AGENTS_COMPLAINTS.md` (225 KB) into a single unified file inside `C:\Users\anton\Sync\Reports\AGENTS_COMPLAINTS.md`.
2. **Redirect Active Script Writes:** Update `agent_listener.py`, `sensors.py`, and `reasoning_engine.py` to:
   - Write/read all log files (like `agent.log`, `heartbeat.log`, `whatsapp_bridge.log`) directly in `C:\Users\anton\Sync\logs/` instead of `/Scripts/`.
   - Write/read database/chat records (like `ai_chat_room.txt` and `whatsapp_messages.txt`) directly in `C:\Users\anton\Sync\Data/` instead of `/Scripts/`.
   - Write agent complaints directly to `/Reports/AGENTS_COMPLAINTS.md`.
3. **Delete Redundant Duplicates:** Safely remove duplicate files from the root and `/Scripts/` directories once moved/redirected.
4. **Merge Logs Directories:** Configure `cleaner.py` and all other scripts to use the unified `C:\Users\anton\Sync\logs/` folder instead of creating a secondary `/Scripts/logs/` folder.

## Context, Memory & Existing Tools
- **Rule of Structure:** `SYNC_STRUCTURE.md` strictly forbids putting non-config files in the root of `C:\Users\anton\Sync`.
- **Files Involved:**
  - `agent_listener.py`, `sensors.py`, `reasoning_engine.py`, `cleaner.py`, `test_dependencies.py`.
- **Duplicates to Remove:**
  - Root: `AGENTS_COMPLAINTS.md`, `agent.log`, `ai_chat_room.txt`, `client_secret.json`, `credentials.json`, `google_token.json`, `whatsapp_messages.txt`, `PLAN.md` (will be moved to `/Docs/PLAN.md` or updated).
  - Scripts: `AGENTS_COMPLAINTS.md`, `ai_chat_room.txt` (which is 8 MB, must be moved to `/Data`), `whatsapp_messages.txt`.

## Step-by-Step Strategy

### Step 1: Merge and Consolidate AGENTS_COMPLAINTS.md [TODO]
- Read the content of the three complaints files.
- Combine their historical contents into a single unified log, sorted/merged cleanly.
- Write the final consolidated file to `C:\Users\anton\Sync\Reports\AGENTS_COMPLAINTS.md`.
- Delete `C:\Users\anton\Sync\AGENTS_COMPLAINTS.md`, `C:\Users\anton\Sync\Scripts\AGENTS_COMPLAINTS.md`, and `C:\Users\anton\Sync\logs\AGENTS_COMPLAINTS.md`.

### Step 2: Relocate Data Files to `/Data` [TODO]
- Move the active 8 MB chat log `ai_chat_room.txt` from `/Scripts/` to `C:\Users\anton\Sync\Data\ai_chat_room.txt`.
- Move `C:\Users\anton\Sync\whatsapp_messages.txt` to `C:\Users\anton\Sync\Data\whatsapp_messages.txt`.
- Delete legacy duplicate `ai_chat_room.txt` from the root of Sync.

### Step 3: Update Paths in Active Scripts [TODO]
- **`agent_listener.py`**:
  - Update `CHAT_FILE` to `C:\Users\anton\Sync\Data\ai_chat_room.txt`.
  - Update `LIVE_CHAT_FILE` to `C:\Users\anton\Sync\Data\.gmc_live_chat.txt` or `.gmc_live_chat.txt` in `/Data`.
  - Update `COMMAND_FILE` to `C:\Users\anton\Sync\Data\agent_commands.txt`.
  - Update `COMMAND_OFFSET_FILE` to `C:\Users\anton\Sync\Data\.agent_commands.offset`.
  - Update `CONTROL_FILE` to `C:\Users\anton\Sync\Data\agent_control.json`.
  - Update `complaints_file` to `C:\Users\anton\Sync\Reports\AGENTS_COMPLAINTS.md`.
  - Update log file paths (`agent.log`, `heartbeat.log`, etc.) to point to `C:\Users\anton\Sync\logs/`.
  - Update `wa_file` to `C:\Users\anton\Sync\Data\whatsapp_messages.txt`.
- **`sensors.py`**:
  - Update `chat_file` and `wa_file` paths to look inside `C:\Users\anton\Sync\Data/`.
  - Update log paths to `C:\Users\anton\Sync\logs/`.
- **`reasoning_engine.py`**:
  - Update `chat_path` and `wa_path` to `/Data/`.
- **`cleaner.py`**:
  - Update targeted log files list to search directly in `C:\Users\anton\Sync\logs/` instead of `/Scripts/`.
  - Remove references to `/Scripts/logs`.
- **`test_dependencies.py`**:
  - Update dependency verification path references.

### Step 4: Remove Redundant OAuth Duplicates [TODO]
- Delete `google_token.json`, `client_secret.json`, and `credentials.json` from the root of `C:\Users\anton\Sync` (keeping the primary functional ones safely in `C:\Users\anton\Sync\Scripts\`).

### Step 5: Verify & Restart Daemons [TODO]
- Compile check all updated scripts (`python -m py_compile Scripts/*.py`).
- Safely restart the `agent_listener.py` daemon so it operates with the clean directory paths.

## Self-Healing Tools
- Syntax and compilation check: `python -m py_compile Scripts/agent_listener.py` and other modified scripts.
- Runtime sanity checking by running the listener logic and checking that new logs are written to the right locations.
