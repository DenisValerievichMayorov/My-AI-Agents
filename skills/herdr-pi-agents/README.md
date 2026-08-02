# herdr-pi-agents

Навык управления **cloud pi-агентами** в Herdr (OpenRouter / NVIDIA / ollama-cloud).

Локальные модели (Ollama `granite4`, `phi4-mini`, LM Studio) **удалены 2026-08-02**.

## Для кого
- Grok
- agy (оркестратор)
- Другие агенты, которым нужно делегировать работу на дешёвые **cloud** модели

## Быстрый старт

```powershell
. "C:\Users\anton\Sync\skills\herdr-pi-agents\scripts\load-pi-aliases.ps1"
pi-launch pi-orfree tencent/hy3:free -Provider openrouter
pi-send pi-orfree "Задача..."
pi-wait pi-orfree
pi-read pi-orfree 60
```

## Основные файлы
- `SKILL.md` — полная документация
- `scripts/pi-send-task.ps1` — отправка задачи + Enter
- `scripts/pi-wait.ps1` — ожидание завершения
- `scripts/load-pi-aliases.ps1` — алиасы

## Связанные навыки
- herdr-multi-pi-launch — cloud bulk launch
- herdr-integration — команды Herdr
- herdr-pi-protocol — протокол отчётов
