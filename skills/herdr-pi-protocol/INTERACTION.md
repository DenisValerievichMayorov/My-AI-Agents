# Инструкция взаимодействия: master + оркестратор + pi-агенты

**Дата:** 2026-07-15  
**Среда:** Herdr, вкладка `Agents+Orch`, workspace `w2`  
**Проверено:** collab smoke + rename fix

---

## 0. Снимки состояния для master (время / очерёдность)

Оркестратор пишет **timestamped screen**, чтобы Grok видел порядок и устаревание:

| Файл | Назначение |
|------|------------|
| `Sync/Data/orch_status_latest.json` | последний снимок (`screen_ts`, `screen_unix`, agents) |
| `Sync/Data/orch_status_latest.md` | то же human-readable |
| `Sync/Data/orch_to_master.jsonl` | лента событий: `seq`, `ts`, `unix`, `kind`, `label`, `text` |

**Правила для master (Grok):**
1. Перед решением читай `orch_status_latest.json`.
2. Если `now - screen_unix > 180` — снимок **устарел**, сделай `herdr pane list` сам.
3. События упорядочивай по `seq` / `unix`, не по порядку появления в чате.
4. Сообщения вида `[orch-screen ts=YYYY-MM-DDTHH:MM:SS unix=…]` — это метка **времени снимка**, не «шум».

## 1. Роли

| Роль | Herdr name (send) | Label панели (видно) | Модель |
|------|-------------------|----------------------|--------|
| **Master** | `agy-main` | `Grok · master` | Grok 4.5 |
| **Watchdog** | `orch-hy3` | `ORCH · hy3` | monitor LLM: `tencent/hy3:free` |
| **Worker A** | `hy3-orfree` | `tencent/hy3 · orfree` | **tencent/hy3:free** via `pi -p` |
| **Worker B** | `hy3-interactive` | `tencent/hy3 · interactive` | **tencent/hy3:free** interactive |

Переименовать/восстановить:
```powershell
powershell -File Sync/skills/herdr-orchestrator/scripts/ensure_agent_names.ps1
```

### Приоритет моделей (канон)
1. **`tencent/hy3:free`** — основной (OpenRouter)  
2. `openrouter/free` — auto-router  
3. `qwen/qwen3-coder:free` / gemma free — только если 1–2 недоступны (часто 429)

**Правило:** `herdr agent send` принимает **name** (после `agent rename`) или **pane_id**.  
**НЕ** принимает один только label, если name не выставлен → `agent_not_found`.  
Все pi без rename = agent type `pi` → **ambiguous**.

После любого рестарта сессии / вкладки:
```powershell
powershell -File Sync/skills/herdr-orchestrator/scripts/ensure_agent_names.ps1
```

---

## 2. Канонический send (с Enter)

`herdr agent send` **только вставляет текст**, Enter сам **не** жмёт.

```powershell
# Надёжный паттерн (предпочтительно pane_id)
$pane = "w2:p3K"   # или resolve из herdr pane list
herdr pane send-keys $pane Ctrl+c          # сброс мусора в input
Start-Sleep -Milliseconds 250
herdr agent send $pane "ЗАДАЧА..."
Start-Sleep -Milliseconds 300
herdr pane send-keys $pane Return          # ОБЯЗАТЕЛЬНО
```

По имени (после ensure_agent_names):
```powershell
herdr agent send pi-nemotron "ЗАДАЧА..."
herdr pane send-keys (herdr agent get pi-nemotron | ConvertFrom-Json | % { $_.result.agent.pane_id }) Return
```

Альтернатива: `herdr pane run <pane_id> <command>` — для shell-команд (не для chat-промпта pi).

---

## 3. Контракт задачи → RESULT

Каждая задача worker'у должна требовать:

```
RESULT: <SHORT_CODE> [key=value ...]
```

Пример:
```
RESULT: NEMO-FILE-OK path=C:\Users\anton\Sync\Data\collab_tests\token_a_....txt
```

Worker **после** результата:
1. Пишет `RESULT:` в stdout панели (обязательно).
2. Опционально шлёт master (текст, **без** Return на busy master):
   ```powershell
   herdr agent send agy-main "pi-orfree | RESULT: ..."
   # НЕ делать send-keys Return на agy-main если Grok mid-turn
   ```
3. Wiki-лог: append в `C:/Users/anton/wiki/raw/agent_logs.md`.

---

## 4. Оркестратор (granite)

Скрипт: `Sync/Skills/token-orchestrator/scripts/herdr_orchestrator.py`  
Лог (если фон): `Sync/Data/herdr_orchestrator.log`  
В панели: `python -u .../herdr_orchestrator.py`

| Наблюдает | Действие |
|-----------|----------|
| working / spinner | NO ACTION |
| `~ (main)` idle | NO ACTION (не спамить учебными задачами) |
| idle + RESULT/Took | REPORT TO MASTER: `agent send` + **Return (Enter)** на agy-main (без Enter текст только в input) |
| PS prompt без pi | RESTART pi (`-ne` + tools) |
| rate/429 | REPORT TO MASTER |
| DELEGATE | только при явной TASK; send на **pane_id** + Return |

LLM анализа: `openrouter/tencent/hy3:free`; иначе rule-based (локальный Ollama снят).

---

## 5. Master (Grok / agy-main)

Перед делегированием:
1. `herdr pane list` + `herdr agent list`
2. `ensure_agent_names.ps1` если names пропали
3. Не делегировать в agent со status `working` без причины (interrupt)
4. Короткие задачи; CH>90% → `/new` или рестарт pi
5. После send — ждать idle / `RESULT:` через `herdr pane read` или `herdr agent wait <pane> --status idle`

Smoke:
```powershell
powershell -File Sync/skills/herdr-orchestrator/scripts/collab_smoke_test.ps1
```

---

## 6. Запуск pi (канон)

### pi-nemotron (interactive OK)
```powershell
pi -ne --provider openrouter --model tencent/hy3:free --tools read,bash,edit,write,grep,find,ls
```

### pi-orfree (ВАЖНО — tools fix 2026-07-15)
Interactive `tencent/hy3:free` в Herdr **ломает tools**: пишет fake XML `<tool_call>` вместо native pi tools.  
**Рабочий режим:** host `pi -p` (non-interactive):

```powershell
powershell -File Sync/skills/herdr-orchestrator/scripts/send_orfree_task.ps1 -Prompt "задача..." -ShowInPane
```

Не слать tool-задачи через `herdr agent send pi-orfree` в interactive chat.

- **`-ne`**: защита от конфликтов packages (web_search)
- **Полные tools** (не `--no-tools`) для worker'ов
- CDP браузер: `http://localhost:9222` (профиль Denis) — **не** `chromium.launch()`

---

## 7. Layout (одно окно)

Вкладка **Agents+Orch** 2×2:

```
[ agy-main              | pi-orfree     ]
[ granite-orchestrator  | pi-nemotron   ]
```

Zoom off. Pane id плавают — всегда `herdr pane list`.

---

## 8. Частые ошибки (и фикс)

| Ошибка | Причина | Фикс |
|--------|---------|------|
| `agent_not_found` pi-orfree | name не задан, label ≠ target | `ensure_agent_names.ps1` или pane_id |
| `agent_target_ambiguous` pi | три pi без name | rename |
| Текст в input, агент не стартует | забыли Enter | `pane send-keys Return` |
| `х` / мусор перед промптом | грязный input buffer | Ctrl+c перед send |
| Master «ломается» mid-turn | orch/agent жмёт Return master | report **без** Return |
| CH 95–99% | длинная сессия | рестарт pi / compact |
| (legacy) Ollama connection error | local Ollama removed | use cloud openrouter only |
| Extension web_search conflict | два пакета | убран `pi-web-access`; `-ne` |
| agent send label в orch | старый код | orch шлёт на pane_id |

---

## 9. Минимальный протокол цикла

```
Master: ensure names → snapshot → send task A (nemo) + Enter
Master: send task B (orfree) + Enter  [или после RESULT A]
Orch:   monitors → REPORT when RESULT
Worker: tools → artifact → RESULT: line
Master: read panes / artifacts → wiki log → next task
```

---

## 10. Файлы

| Файл | Назначение |
|------|------------|
| `Sync/skills/herdr-pi-protocol/INTERACTION.md` | этот документ |
| `Sync/skills/herdr-pi-protocol/SKILL.md` | CDP + report rules |
| `Sync/skills/herdr-orchestrator/scripts/ensure_agent_names.ps1` | rename |
| `Sync/skills/herdr-orchestrator/scripts/collab_smoke_test.ps1` | smoke |
| `Sync/Skills/token-orchestrator/scripts/herdr_orchestrator.py` | watchdog |
| `Sync/Data/collab_tests/` | артефакты smoke |
