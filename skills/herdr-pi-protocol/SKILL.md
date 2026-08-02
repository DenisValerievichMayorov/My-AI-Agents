---
name: herdr-pi-protocol
description: Протокол работы pi-агентов внутри Herdr-оркестрации. Покрывает CDP-скрапинг, отправку отчётов оркестратору (agy) и автоматический Enter. Обязателен для всех pi-агентов в white-list (pi-nemotron, pi-nv20, pi-orfree).
---

# Herdr Pi-Agent Protocol

## 1. Правило инструментов — CDP вместо Playwright

**ЗАПРЕЩЕНО**: использовать Playwright, puppeteer-launch, chromium.launch().  
**ОБЯЗАТЕЛЬНО**: использовать `chrome-remote-interface` (CDP) напрямую.

Chrome запущен на **порту 9222** с профилем Denis Maiorov.

Скрапер уже написан:
```bash
node C:/Users/anton/agent_tools/scrape_candy_smart_cdp.js [запрос]
```
Примеры:
```bash
node C:/Users/anton/agent_tools/scrape_candy_smart_cdp.js 'candy 40 cm'
node C:/Users/anton/agent_tools/scrape_candy_smart_cdp.js 'candy smart wasmachine'
node C:/Users/anton/agent_tools/scrape_candy_smart_cdp.js   # все запросы по умолчанию
```

---

## 2. Правило отчётности — два шага, без паузы

После завершения любой задачи **сразу** выполни два bash-вызова подряд:

### Шаг 1 — отправить отчёт оркестратору:
```bash
herdr agent send agy "Краткий итог задачи на русском"
```

### Шаг 2 — нажать Enter в терминале agy:
```bash
herdr pane send-keys w2:p1X Return
```

**Объединённый вызов (рекомендуется):**
```bash
herdr agent send agy-main "твой отчёт"
# Return на master — только если master idle (не mid-turn у Grok)
```

> ⚠️ Без `send-keys Return` сообщение попадает в буфер agy, но оркестратор его не получит автоматически.

---

## 3. Правило выполнения — без комментариев перед tool call

**ЗАПРЕЩЕНО**:
```
Сейчас я запущу скрипт. Вот моя команда: ...
```

**ОБЯЗАТЕЛЬНО**: сразу вызывать bash-инструмент без вводного текста.

Если нужно объяснение — пиши ПОСЛЕ выполнения, не до.

---

## 4. Правило отчёта — структура

**Канон mesh (все задачи):** skill `mesh-quality-gate` + `AGENTS.md` §12–15, §20.  
Перед «готово» обязателен блок **VERIFY**.  
Scrape/UI: browser-smoke CDP :9222 (не `chromium.launch`).  
≥2 tracked-файла: `REVIEW` pass другим агентом (или skip-by-user).  
Однострочный формат для быстрых scrapes допустим, но VERIFY/RC обязателен.

### 4.1 Универсальный mesh-отчёт (предпочтительно)
```text
TASK: <задача>
AGENT: <pi-orfree|pi-nemotron|...>
SCOPE: <path или URL-scope>
DONE: <факты>
VERIFY: <команда → RC | N/A reason>
REVIEW: <self-only | pending | pass by <agent> | skip-by-user>
RISK: <none|...>
NEXT: <done|follow-up>
```

### 4.2 Короткий формат для price/scrape-задач
Отчёт оркестратору должен содержать:
- Имя агента
- Запрос / задача
- Количество найденных кандидатов
- Ключевые результаты (цена, ссылка, размеры если есть)
- RC (exit code) **= VERIFY** (+ CDP OK если scrape)

Пример хорошего отчёта:
```
pi-orfree | candy smart wasmachine | Найдено: 2 | CS148TW4 €315 Schaarbeek 58cm | Grand O Vita €175 Sint-Laureins глубина не указана | VERIFY RC=0 CDP:9222 OK
```

---

## 5. White-list агентов и их ID в Herdr

| Агент | Pane ID (актуально 2026-07-15) | Модель |
|-------|---------|--------|
| pi-nemotron | w2:p3K | openrouter nvidia/nemotron-3-super-120b-a12b (или tencent/hy3:free) |
| pi-orfree | w2:p3J | tencent/hy3:free |
| agy-main / grok | w2:p31 | Grok (master) |
| granite-orchestrator | w2:p3N | herdr_orchestrator.py (daemon) |

> Pane ID плавают при пересоздании вкладок — всегда бери актуальные через `herdr pane list`.

---

## 6. Если herdr не найден в PATH

Добавь в PATH перед запуском:
```bash
export PATH="$PATH:/usr/local/bin"
herdr agent send agy "сообщение" && herdr pane send-keys w2:p1X Return
```

Если всё равно не работает — выведи результат в stdout, оркестратор прочитает через `herdr pane read`.

---

## 7. Установка скилла

```bash
# На PC (PowerShell):
npx skills add C:/Users/anton/Sync/Skills/herdr-pi-protocol -g -y --copy

# На Termux / Linux:
npx skills add ~/Sync/Skills/herdr-pi-protocol -g -y --copy
```

---

## 8. ADB-подключение к телефону Дениса

**ADB путь** (Git Bash / Windows): `/c/Users/anton/platform-tools/adb.exe`  
**Телефон**: Motorola Edge 50 Fusion  
**IP (локальная сеть)**: `192.168.1.2:5555`  
**IP (Tailscale)**: `100.87.207.25`  

### Подключение и проверка:
```bash
/c/Users/anton/platform-tools/adb.exe connect 192.168.1.2:5555
/c/Users/anton/platform-tools/adb.exe devices
```

### Пример — поставить будильник:
```bash
ADB="/c/Users/anton/platform-tools/adb.exe"
$ADB connect 192.168.1.2:5555
$ADB shell am start -a android.intent.action.SET_ALARM \
  -e android.intent.extra.alarm.HOUR 12 \
  -e android.intent.extra.alarm.MINUTES 40 \
  --ez android.intent.extra.alarm.SKIP_UI true
```

> ⚠️ После каждого перезапуска adb-daemon нужно переподключаться через `connect`.

---

## 9. Анализ изображений и чеков из чатов (OCR)

Если в логах WhatsApp есть отсылка к медиафайлу (например, `[Media: 1783544280169.jpg]`), агент **обязан** проанализировать текст на изображении:
1. Изображения сохраняются в папке `C:\Users\anton\Sync\whatsapp_media\` (или `~/Sync/whatsapp_media/` на Termux).
2. Проверьте, существует ли уже готовый текстовый файл расшифровки, например `C:\Users\anton\Sync\whatsapp_media\1783544280169.jpg.txt`. Если он есть, просто прочитайте его содержимое.
3. Если файла расшифровки нет, запустите OCR-утилиту:
   ```bash
   node C:/Users/anton/agent_tools/ocr_helper.js "C:/Users/anton/Sync/whatsapp_media/1783544280169.jpg"
   ```
   Утилита автоматически распознает текст (с поддержкой nld, rus, eng) и создаст `.txt` файл.
4. Проанализируйте полученный текст счета, чека или расписания и используйте его для решения задачи.
