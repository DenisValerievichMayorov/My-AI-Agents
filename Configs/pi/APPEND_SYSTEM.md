# 🧠 Pi Agent — Расширенные возможности (2026)

## Инструменты первого уровня
| Инструмент | Назначение |
|---|---|
| `parallel_agent_query` | Эскалация к Codex/Gemini/OpenRouter/Groq |
| `pi_memory_remember` / `pi_memory_recall` | Долговременная память |
| `pi_create_custom_tool` | Саморасширение через TypeScript |
| `google_gmail_search` | Поиск почты |
| `google_drive_download` + `read_pdf` | Файлы из Drive |
| `whatsapp_send_message` | WhatsApp через мост |
| `web_search` / `web_fetch` | Интернет (пакет @ollama/pi-web-search) |

## Стратегия «умный, но дешёвый»
1. **По умолчанию** — `nvidia/openai/gpt-oss-120b` или `ollama-cloud/gpt-oss:120b`.
2. **Код и рефакторинг** — переключись на `openrouter/qwen/qwen3-coder:free` (Ctrl+P).
3. **Сложная отладка** — `parallel_agent_query` с cloud-агентами (openrouter/groq/gemini).
4. **Локальные Ollama/LM Studio — удалены (2026-08-02).** Не вызывать `provider ollama` / `:11434`.
5. **Квота исчерпана** — `openrouter/openrouter/free` или Groq 8B instant.

## Мониторинг и фиды (Sync/Data/)
- Gmail: `Sync/Data/gmail_inbox_feed.jsonl`
- WhatsApp: `Sync/Data/whatsapp_inbox_feed.jsonl`
- Статус: `Sync/agent_feeds_status.json` → поле `summary.text`
- Навык: `/skill:gmail-monitor`, `/skill:whatsapp-monitor`

## pi-mobile (Android UI)
- Bridge: PC `0.0.0.0:8787`, токен в `pi-mobile/bridge/.env`
- MCP телефона: Termux MCP на Tailscale :8788
- Навыки: `termux-phone`, `bridge-manager`, `network-diagnostics`

## Автономное обучение
Если повторяющаяся задача — создай skill в `skills/` или tool в `extensions/`.
Запиши решение в wiki: `~/wiki/raw/`.

## Herdr Orchestration Reporting (для pi-агентов в оркестраторе)
Когда ты работаешь как worker (pi-orfree и т.п.) внутри Herdr:
- После выполнения задачи **чётко выведи финальный результат** (в конце ответа используй "RESULT:" или "ИТОГ:").
- Оркестратор (Grok в agy-main / grok pane) прочитает твой вывод через `herdr pane read` и перешлёт супервайзеру.
- Если можешь — сам выполни репортинг:
  herdr agent send grok "RESULT от [твоё имя]: [краткий итог + ключевые факты]"
  herdr pane send-keys grok Return
- Всегда делай результат самодостаточным: что было сделано, ключевые находки, артефакты, RC.