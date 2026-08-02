# Rules hygiene (living memory)

Inspired by Boris Cherny / Claude Code: short living rules file + update on repeated mistakes.

## Root vs skill vs wiki

| Layer | What belongs here |
|-------|-------------------|
| `AGENTS.md` (root) | Invariants only; target ≤~220 lines |
| Skills (`Sync/skills/...`) | Checklists, scripts, templates, how-to |
| Wiki (`wiki/raw` → ingest) | Decisions, incidents, durable ops facts |

## 2nd-error rule

If an agent makes the **same class of mistake twice** (wrong path, skipped VERIFY, empty chromium.launch, missing Enter on herdr, etc.):

1. Do **not** only re-prompt in chat.
2. Write a durable rule:
   - short bullet in the relevant skill, **or**
   - note in `C:/Users/anton/wiki/raw/` then `ingest → autolink → lint → website`
3. Prefer **imperatives**: «Never X; always Y» over narrative.

## What not to do

- Paste entire skill into AGENTS.md
- Grow root with one-off project details
- Rely on chat memory for multi-session ops facts

## Conflict order

safety confirm (AGENTS §18) > isolation (§13) > VERIFY (§12) > convenience
