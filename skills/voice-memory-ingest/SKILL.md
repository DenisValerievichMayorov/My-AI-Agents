---
name: voice-memory-ingest
description: Convert recorder audio into persistent personal memory artifacts for agents using the local whisper.cpp and post-processing pipeline. Use when the user asks to ingest voice recordings, transcribe audio into memory candidates, or update personal memory from recorder files.
---

# Voice Memory Ingest Skill

Use this skill when the user wants to turn recorder audio into persistent personal memory for agents.

## Canonical Store

Primary synced memory root:

`C:\Users\anton\Sync\Data\PersonalMemory`

Codex mirror/pointer:

`C:\Users\anton\.codex\memories\personal_memory`

## Pipeline

1. Transcribe audio locally with `whisper.cpp` CUDA and `ggml-large-v3-turbo.bin`.
2. Post-process the transcript with OpenRouter (local Ollama removed 2026-08-02).
3. Save raw transcript, JSON, summary, and memory candidates.
4. Treat all extracted facts as candidates until the user confirms them.

## Command

From `C:\Users\anton\Desktop\Aanslagbilet`:

```powershell
python .\audio_memory_ingest.py "D:\REC\01_20250728224423.wav"
```

For a test slice:

```powershell
python .\audio_memory_ingest.py "D:\REC\01_20250728224423.wav" --duration-minutes 5
```

## Reading Protocol

Before using personal context, agents should read:

1. `C:\Users\anton\Sync\Data\PersonalMemory\README.md`
2. `C:\Users\anton\Sync\Data\PersonalMemory\core\profile.md`
3. `C:\Users\anton\Sync\Data\PersonalMemory\memories\memory_candidates.jsonl`

## Safety Rules

- Do not store conflict claims as established facts.
- Mark emotional or disputed claims as `со слов участников`.
- Prefer concise memory entries over raw transcript recall.
- Keep source links to transcripts for auditability.
- Ask the user before promoting candidates into stable profile facts.
