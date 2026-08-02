---
name: mesh-quality-gate
description: >
  Протокол зрелости Step 2 (Parallel/Orchestrator) для домашней mesh-системы.
  DoD + VERIFY gate (вкл. browser CDP smoke), изоляция worktree, mesh-отчёт,
  plan-before-edit, default Author≠Reviewer (≥2 files), rules hygiene,
  маршрутизация моделей, idle policy, permission tiers.
  Триггеры: DoD, VERIFY, mesh report, worktree, оркестратор, quality gate,
  «готово», приёмка, browser smoke, CDP, /mesh-quality-gate, step 2, вайбкодинг.
---

# Mesh Quality Gate (Step 2 Parallel)

Канон политики: `C:/Users/anton/AGENTS.md` §11–20.  
Этот skill — операционные шаблоны и чеклисты. **Не подменяет** safety rules (shutdown, mail/WA, force-push).

## Когда применять

- Любая подзадача в mesh (Grok, pi, agy, subagent).
- Перед словами «готово» / «done» / «закрываю задачу».
- При делегировании (orchestrator brief).
- Когда хочется «просто вайбкоднуть» без проверок — **стоп**, включить gate.

## 1. Быстрый чеклист исполнителя

```
[ ] Есть GOAL + SCOPE_PATH (если нет — запросить, не гадать по C:\Users\anton)
[ ] Plan-before-edit, если ≥2 файла / >1ч / риск
[ ] Сделал работу только в SCOPE
[ ] VERIFY прогнан (команды + RC) или N/A с причиной
[ ] UI/web? → browser-smoke CDP :9222 (см. §4 + references/browser-verify.md)
[ ] ≥2 tracked-файла? → REVIEW_REQUIRED (Author ≠ Reviewer) до «готово»
[ ] Mesh-отчёт по шаблону отправлен REPORT_TO
[ ] Durable-знание → wiki (если решение/операционный факт)
[ ] 2nd-error? → записать в skill/wiki, не только в чат
[ ] Нет pending destructive без confirm пользователя
```

## 2. Mesh-отчёт (обязательный)

Копипаст:

```text
TASK: 
AGENT: 
SCOPE: 
DONE: 
VERIFY: 
REVIEW: <self-only | pending | pass by <agent> | skip-by-user>
RISK: 
NEXT: 
```

Файл-шаблон: `templates/mesh-report.md`.

### Примеры VERIFY

```text
VERIFY: node --check script.js → 0; wiki lint → 0
VERIFY: Get-Service Tailscale → Running; FAIL: tests missing → RISK noted
VERIFY: N/A research-only (no file changes)
VERIFY: browser-smoke CDP :9222/json/version → Browser=Chrome/...; page title="..." → OK
VERIFY: FAIL CDP:9222 offline; not done
```

## 3. Бриф оркестратора

Шаблон: `templates/task-brief.md`.

Минимум полей: GOAL, SCOPE_PATH, BRANCH_OR_WORKTREE, OUT_OF_SCOPE, DoD, VERIFY, MODEL_HINT, REPORT_TO.  
При multi-file: `REVIEW_REQUIRED: yes` + кто reviewer.

## 4. Browser VERIFY (CDP smoke)

**Когда обязательно:** scraper, web UI, Playwright/Puppeteer, правка страниц/дашбордов, «проверь в браузере».

**Минимум (AGENTS.md §12.2 + §7):**

| # | Check | Pass |
|---|--------|------|
| 1 | CDP up | `GET http://localhost:9222/json/version` → 200 + Browser JSON |
| 2 | Connect mode | только `chromium.connectOverCDP('http://localhost:9222')` + `contexts()[0]` |
| 3 | No empty profile | **запрет** `chromium.launch()` / `newContext()` для стандартных задач |
| 4 | Observable fact | URL + title **или** selector/text **или** status code в VERIFY |

Скрипт smoke (без Playwright):

```powershell
powershell -File Sync/skills/mesh-quality-gate/scripts/browser-cdp-smoke.ps1
```

Детали: `references/browser-verify.md`.

## 5. Default Author ≠ Reviewer

| Изменение | Review |
|-----------|--------|
| 1 tracked-файл, trivial | self-VERIFY OK; review optional |
| **≥2 tracked-файла** | **REVIEW_REQUIRED** — другой агент / master + `review` / `check-work` |
| security / money / mail-WA / shutdown | always REVIEW_REQUIRED (+ plan-before-edit) |
| Skip | только явное «skip review» от пользователя |

1. Author: DONE + VERIFY (свои тесты).
2. Reviewer: read-only + перегон VERIFY; **не** дописывает фичу в том же ходе.
3. «Готово» только после `REVIEW: pass` или skip-by-user.

## 6. Rules hygiene

| Правило | Действие |
|---------|----------|
| Root `AGENTS.md` | инварианты, ориентир ≤~220 строк |
| Длинные чеклисты/примеры | skills + wiki, не root |
| **2nd-error** | повтор той же ошибки агента → skill / `wiki/raw` → ingest |
| Конфликт | safety §18 > isolation §13 > VERIFY §12 > convenience |

Детали: `references/rules-hygiene.md`.

## 7. Изоляция

| Параллель | Правило |
|-----------|---------|
| 1 агент, мелкий фикс | Можно cwd репо |
| ≥2 агента на код | 1 agent = 1 worktree **или** 1 branch |
| Wiki | raw → ingest; не драться за один source-файл |
| Sync git | `git-sync-protocol` |

Grok: `spawn_subagent` + `isolation: worktree` когда правят один git-проект параллельно.

## 8. Model routing + Agent route

| MODEL_HINT | Кто |
|------------|-----|
| `plan` | Grok / agy / strong model |
| `implement` | pi / cheap coder |
| `review` | отдельный pass, не author |
| `explore` | read-only explore subagent |

**Куда слать задачу (SELF vs spawn vs Herdr):** skill **`agent-route`**  
`Sync/skills/agent-route/scripts/route-decision.ps1` → JSON `route` + `fallback`.  
В mesh-отчёт добавляй: `ROUTE: SELF|GROK-SUBAGENT|HERDR-PI|AGY`.

См. также `token-orchestrator` (cloud-only; без локального Ollama/Codex).

## 9. Idle (нет user-task)

Приоритет: help mesh → audit last changes → wiki health → sync-watchdog/system-maintenance (non-destructive) → log only if useful.

## 10. Permission tiers (кратко)

- **Auto:** read, edit in scope, test/lint, wiki pipeline, mesh reports, CDP smoke.
- **Confirm:** rm -rf, force-push, shutdown, outbound mail/WA/TG, payments, disable security.

Полный список: AGENTS.md §18.

## 11. Скрипты

```powershell
# Заготовка отчёта
powershell -File Sync/skills/mesh-quality-gate/scripts/new-mesh-report.ps1 -Task "fix-x" -Agent "grok"

# Browser CDP smoke
powershell -File Sync/skills/mesh-quality-gate/scripts/browser-cdp-smoke.ps1
```

## 12. Связанные skills

- `token-orchestrator` — кого звать
- `herdr-pi-protocol` — send report + Enter
- `wiki-logger` / `wiki-pipeline` — durable memory
- `check-work` / `review` — приёмка (default multi-file)
- `git-sync-protocol` — Sync repo hygiene
