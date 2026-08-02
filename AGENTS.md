# Global Agent Wiki Integration Protocol

Canonical file: `C:/Users/anton/AGENTS.md` (PC) · `~/Sync/AGENTS.md` (Termux / Chromebook penguin).

All AI agents, CLIs, and sub-agents must use the local LLM Wiki to keep context and project continuity.

## 1. Canonical Wiki Location
- The canonical wiki workspace is `C:/Users/anton/wiki` (PC) or `~/wiki` (Termux / penguin).
- `C:/Users/anton/wiki` is the stable root-level entrypoint for the wiki.
- The legacy path `C:/Users/anton/Desktop/TV` may still exist for compatibility, but new instructions and automation must use `C:/Users/anton/wiki`.

## 2. Always Consult the Wiki First
- Before beginning any task, research, code change, system change, or project modification, inspect `index.md` in the wiki vault.
- From the wiki root, run `node scripts/stats.js` to check wiki health.
- When the task has a topic, also run `node scripts/search.js "<query>"` to locate existing context, decisions, and task history.

## 3. Document New Knowledge
- When resolving a task, fixing a subtle bug, changing architecture, installing/configuring tools, or discovering useful operational context, write it into the wiki.
- Add source material to `wiki/sources/` or a raw note to `raw/`.
- Then run from the wiki root:
  1. `node scripts/ingest.js`
  2. `node scripts/autolink.js`
  3. `node scripts/lint.js`
  4. `node scripts/website.js`

## 4. Personal Context Preference
- Respond in Russian unless explicitly asked otherwise.
- Be concise, direct, and prioritize working code, automation, and verifiable results.
- Prefer using the wiki over chat memory for durable decisions and project context.

## 5. Mobile Agent Logging
All mobile agents (Droid CLI, Termux Pi-agents, Chromebook penguin) MUST log their status, summaries, and actions to the wiki. Write logs to `~/wiki/raw/agent_logs.md` (Syncthing folder Wiki → `~/wiki`).

## 6. Token Orchestrator Mode (Default)
All Grok Build sessions (PC, Termux, Chromebook penguin) and Cursor agents MUST act as **orchestrators by default**, not monolithic executors.

- **Skill:** `Sync/skills/token-orchestrator/SKILL.md` (auto-invoke on every task).
- **Flow:** assess complexity → decompose → delegate (subagents / CLI) → synthesize → deliver concise result.
- **Grok Build:** use `spawn_subagent` (`explore` for research, `general-purpose` for implementation, `plan` for planning).
- **agy (все устройства):** локальный `agy --print` — анализ, аудит, план.
- **pi (опционально):** `pi -p` — реализация на дешёвых моделях.
- **ЗАПРЕЩЕНО:** локальный Ollama/LM Studio, Codex, parallel-agents с Codex.
- **Cursor:** use Task subagents (`generalPurpose`, `code-reviewer`) for search and review.
- **Output:** subagents return compressed reports only; orchestrator never forwards raw logs to the user.
- **Skip delegation** only for trivial (S-level) tasks.

### Device installers
| Device | Command |
|--------|---------|
| PC | `powershell -File Sync/Scripts/install_shared_skills.ps1` |
| Termux | `bash ~/Sync/Scripts/install_shared_skills_termux.sh` |
| Chromebook (penguin) | `bash ~/Sync/Scripts/install_shared_skills_penguin.sh` |
| Any Unix | `bash ~/Sync/Scripts/install_shared_skills_unix.sh` |