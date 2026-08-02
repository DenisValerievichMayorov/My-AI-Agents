---
name: telegram-orchestrator
description: Двусторонний Hermes Telegram-бот для ПК и Termux. Leader election, входящие сообщения → LLM, /status, outbox для уведомлений.
---

# Telegram Orchestrator (Hermes)

Единый бот для общения с агентом из Telegram на телефоне и ПК.

## Возможности

1. **Leader election** — только одно устройство (ПК или Termux) делает polling; нет 409 Conflict.
2. **Входящие сообщения** — обычный текст → `telegram_agent_reply.py` → OpenRouter (Hermes brain; local Ollama removed).
3. **Исходящие** — `hermes_mind.py` шлёт проактивные алерты (сенсоры + кроны); `heartbeat.py` и любой скрипт — через `telegram_outbox.txt`.
4. **Команды**: `/status`, `/ping`, `/help`, `/model`, `/model_cli`.

## Файлы

| Файл | Назначение |
|------|------------|
| `Sync/Scripts/telegram_agent.js` | Основной бот |
| `Sync/Scripts/telegram_agent_reply.py` | Ответ LLM |
| `Sync/Scripts/hermes_mind.py` | Мозг: сенсоры, сон, кроны, проактивный TG |
| `Sync/Scripts/hermes_sensors.py` | 8 сенсоров (feeds, GPS, HASS, Syncthing…) |
| `Sync/Configs/hermes_chronos.json` | Расписание брифингов и think-циклов |
| `Sync/Scripts/telegram_outbox.txt` | Очередь исходящих |
| `Sync/Data/agent_feeds_status.json` | Данные для `/status` |

## Запуск

**Windows (ПК, всё):**
```powershell
C:\Users\anton\Sync\Scripts\start_hermes_full.ps1
```
Входит в `start_all_monitors.ps1` (задача GMC-Agent-Monitors).

**Termux (деплой с ПК):**
```powershell
C:\Users\anton\Sync\Scripts\start_hermes_termux.ps1
```

**Termux (телефон):**
```bash
bash ~/Sync/Scripts/start_telegram_agent_termux.sh
```

## Конфиг

`~/.hermes/.env`:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_USERS` (через запятую)
- `PROACTIVE_TELEGRAM_CHAT_ID` — для проактивных алертов

## Как это работает на двух устройствах

Оба запускают `telegram_agent.js`. Кто первый создал `telegram_agent.lock` в Sync — тот **лидер** и слушает Telegram. Второй ждёт. Если лидер падает или heartbeat старше 90 с — второй забирает lock.

Пишите боту в Telegram — ответит LLM устройства-лидера:
- **Termux:** Grok (`~/grok-termux`) → OpenRouter
- **PC:** OpenRouter → Gemini CLI

Feed WhatsApp/Gmail на Termux: `~/Sync/Data/*.jsonl` (Syncthing или `push_feeds_to_termux.ps1`).
Отправка WA с Termux: `WHATSAPP_BRIDGE_URL=http://100.72.214.118:3000` (мост на ПК).