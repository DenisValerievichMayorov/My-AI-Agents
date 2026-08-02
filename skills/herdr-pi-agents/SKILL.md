---
name: herdr-pi-agents
description: Протокол развёртывания и конфигурирования cloud pi-агентов (OpenRouter/NVIDIA/ollama-cloud). Локальный Ollama/LM Studio не используются (сняты 2026-08-02).
---

# Herdr Pi-Agents Configuration Skill

Координация, запуск и контроль параллельных агентов `pi` на PC (через `herdr`).

## 1. Конфигурация моделей (cloud-only)

Локальные провайдеры (`ollama` @ `:11434`, LM Studio, vLLM local) **удалены**. White-list: `Sync/Configs/pi/white-list.json`.

### Cloud (единственный режим)
- **pi-orfree**: `openrouter/free` / `tencent/hy3:free`
- **pi-nv20**: `nvidia/openai/gpt-oss-20b`
- **pi-nemotron**: `nvidia/nemotron-3-super-120b-a12b`
- **Запуск (Herdr / PowerShell)**:
  ```powershell
  pi -ne --provider openrouter --model tencent/hy3:free --tools read,bash,edit,write,grep,find,ls
  ```
- **`-ne`**: отключает packages/extensions при конфликте tool `web_search` (пакет `@ollama/pi-web-search` — это npm-имя, не локальный сервер).
- **НЕ** использовать `--no-tools` для рабочих pi (AGENTS.md §9).

### Запрещено
```powershell
# НЕ запускать:
pi --provider ollama --model granite4:latest
pi --provider ollama --model qwen2.5-coder:7b
```

---

## 2. Фоновый оркестратор (herdr daemon)

Диспетчер: [herdr_orchestrator.py](file:///C:/Users/anton/Sync/skills/token-orchestrator/scripts/herdr_orchestrator.py)

1. Опрашивает `herdr pane list` каждые 15 с.
2. Читает хвост логов pi-агентов.
3. Анализ: **openrouter/tencent/hy3:free** через `pi -ne -p` (primary); иначе **rule_based_analysis**. Без локального Ollama.
4. Решения: `RESTART` | `PRESS ENTER` | `NO ACTION` | `REPORT TO MASTER`.
5. Лог: `C:/Users/anton/Sync/Data/herdr_orchestrator.log`
6. Старт: `python -u Sync/skills/token-orchestrator/scripts/herdr_orchestrator.py`

---

## 3. Макет интерфейса (Herdr Layout)

См. `herdr-orchestrator/LAYOUT_RULES.md`. После bulk-start: `python Sync/skills/herdr-orchestrator/scripts/herdr_layout_balance.py`.

- `w2:p31` — `agy-main` (master)
- workers — equal columns
- orch daemon — full-width bottom strip (~30–40% height)

```bash
herdr pane send-text <pane_id> "Промпт" && herdr pane send-keys <pane_id> Return
```

---

## 4. Установка скилла

```bash
npx skills add C:/Users/anton/Sync/skills/herdr-pi-agents -g -y --copy
```
