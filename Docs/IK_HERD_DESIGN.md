# ik + Herdr + pi model pool (design)

**Status:** design agreed 2026-08-02 (implementation pending install).  
**Rollback:** each implementation step is a separate git commit in `Sync`.

## Goal
Custom agent **ik** (fork of grok-build) as thin orchestrator:
- launches **herdr** with **pi** workers;
- workers use models from an **ordered pool**;
- on model failure → next model (boundary failover, not mid-turn);
- runs **days** via disk queue + daemon (token cost over wall-clock).

## Layers
1. **ik (master)** — plan, ticket, accept RESULT, failover decision. Few tokens.
2. **Herdr** — panes for pi workers.
3. **Model pool** — ordered free/cloud list + health/cooldown.
4. **Loop daemon** — queue on disk, not infinite chat memory.

## Model pool (v0 order)
See `Configs/pi/white-list.json` + `skills/herdr-orchestrator/MODEL_ROUTING.md`.

1. or-free / ling-3.0-flash:free (tools)
2. or-free / nemotron-3-super free (long)
3. or-free / gpt-oss-20b:free
4. or-free / openrouter/free
5. nvidia / openai/gpt-oss-20b
6. ollama-cloud / minimax-m3

## Failover rules
- Probe → launch pi → wait RESULT.
- Fail: 429, API error, stuck Working, no RESULT, pane dead.
- Action: cooldown model, pick next, re-issue same ticket (cap 3–5).
- Never swap model mid-turn inside one pi session.

## Next implementation steps (each = 1 commit)
1. `model_pool.json` + probe script (no secrets).
2. ik brain endpoint = cloud free (not :11434).
3. herdr ensure 2 workers from pool.
4. ik skill: delegate ticket → RESULT.
5. `ik_herd_loop` dry-run with failover.
6. Task Scheduler / 24h health.

## Commit protocol
See `Docs/STEP_COMMIT_PROTOCOL.md`.
