---
name: parallel-agents
description: "Параллельный опрос cloud-агентов (OpenRouter, Groq, Gemini CLI, OpenCode) и fallback-цепочки. Без локального Ollama."
---

# Parallel Agent Query Skill

Pi-агент запускает параллельный или sequential (fallback) опрос **облачных** моделей и CLI-ассистентов, сводя результаты в один отчёт.

> Локальный Ollama / LM Studio сняты 2026-08-02. Параметр `ollama` / `ollama_model` больше не поддерживается.

## 1. Fallback Mode
* По очереди: OpenRouter → Groq → Gemini CLI (пока не получит успешный ответ).

## 2. Parallel Mode
Одновременно:
  - **OpenRouter** (по умолчанию `qwen/qwen3-coder:free`)
  - **Groq** (`llama-3.1-8b-instant`)
  - **OpenCode CLI** (`opencode run`)
  - **Gemini CLI** (`gemini -p`)
  - **Codex CLI** — только если явно разрешено политикой (обычно **запрещено** token-orchestrator)

## Параметры `parallel_agent_query`
- **`prompt`**: запрос
- **`mode`**: `"parallel"` | `"fallback"`
- **`agents`**: `["openrouter", "groq", "opencode", "gemini"]` (без `ollama`)
- **`openrouter_model`**, **`groq_model`**, **`gemini_model`**
