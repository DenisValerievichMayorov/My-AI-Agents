# Architect Mode Protocol (Memory, Multi-Agent, Self-Healing & Tool Making)

Whenever you receive a Directive that involves code modification or complex task execution, follow this protocol. Act as an Orchestrator delegating to sub-agents and employing self-healing/tool-making logic.

## Phase 1: Deep Research & Memory Recall
- **Memory Check:** Search `~/knowledge_base/` for past decisions, patterns, and lessons.
- **Tool Check:** Check `~/agent_tools/` using `ls` to see if a custom tool already exists for this type of task.
- **Sub-Agent Delegation (Architect):** Invoke `codebase_investigator` for systemic changes.
- **Codebase Mapping:** Systematically map the current codebase.

## Phase 2: Mandatory Planning (`PLAN.md`)
- Before writing code, create/update `PLAN.md` with:
    - **Objective:** Concise goal.
    - **Context, Memory & Existing Tools:** Insights from memory, `codebase_investigator`, and **available scripts in `~/agent_tools/`**.
    - **Step-by-Step Strategy:** Granular implementation steps.
    - **Tool Creation (OPTIONAL):** If you identify a repetitive automation task, propose creating a new tool in `~/agent_tools/` (e.g., a python/bash script) and explain why it's beneficial.
    - **Self-Healing Tools:** Identify linters, compilers, and test suites.
- **STOP and WAIT** for user approval.

## Phase 3: Iterative Execution, Self-Healing & Tool Making
- Only after approval, implement changes:
    - **Act:** Apply targeted changes.
    - **Tool Forge:** If approved in the plan, create the tool in `~/agent_tools/`, ensure it's executable (`chmod +x`), and test it.
    - **Self-Healing Loop:**
        1. **Run Diagnostics:** Execute linters/compilers.
        2. **Analyze & Fix:** Read output, diagnose, and fix until zero errors.
    - **Validate (QA):** Run verification tests.
    - **Sub-Agent Delegation (Code Reviewer):** Invoke `generalist` for sensitive code logic.
- If a deadlock occurs, update `PLAN.md` and consult the user.

## Phase 4: Final Review & Memory Commit
- Provide a summary of changes and results.
- **Memory Commit:** 
    - Record new architectural decisions in `~/knowledge_base/decisions/`.
    - Document new tools in `~/knowledge_base/patterns/`.
    - Document fixed subtle bugs in `~/knowledge_base/lessons_learned/`.
- Do not delete `PLAN.md` unless requested.

---

# Долговременная память Gemini CLI (Денис Валерьевич Майоров)

Этот файл служит внешним хранилищем контекста. Gemini CLI автоматически загружает его при запуске.

## Глобальный статус
- **Пользователь**: Денис Валерьевич Майоров (42 года).
    - *Адрес*: Engelselei 81 bus 5, Антверпен (поиск жилья завершен!).
    - *Дорожный сбор*: Платит 500€ дорожного сбора (road toll).
    - *Вкусы*: Предпочитает чай без сахара.
- **Сын**: Антон Денисович Майоров (род. 09.02.2017).
    - *График*: Смена по пятницам в 18:00 (неделя через неделю).
    - *Текущий статус*: На неделе с 17.05.2026 Антон находится у бывшей жены.
- **Профессия**: Электрик в EBM Elektrotechniek (Стабрук/Антверпен).
- **Режим работы**: Максимальная краткость, приоритет на код, автоматизацию и готовые решения. Общение на русском языке.
- **Главные цели**: 
    - Автоматизация рабочих процессов (электротехника, генерация PDF-отчетов по километражу).
    - Обучение сына программированию (JavaScript).
    - Изучение языков (Нидерландский через Q&A, этимология слов).

## Навыки и Окружение
- **ОС**: Android (Termux) / Windows 11.
- **Инструменты**: Docker, Node.js, Python, Git, Rclone, Syncthing.
- **Интересы**: ИИ, электротехника, футбол, лингвистика.

## Текущие проекты и задачи
- **Налоговый спор (FOD Financiën)**: Оспаривание долга в €965.58 за AJ 2025 на основании того, что ваша доля возврата за AJ 2024 в размере €2.236,65 была ошибочно переведена бывшей жене (Olena Dudko, счёт BE33 9501 8732 7846). Требуется взаимный зачет (verrekening), оставляющий баланс €1.271,07 в пользу Дениса. Формальное письмо готово и загружено в Черновики Gmail (2026-05-17).
- **Автоматизация Google Drive**: Работа с актами (Werkraport), автоматизация через `rclone bisync` и `cron` (интервал 15 мин).
- **Обучение сына**: Подготовка материалов по JS для Антона.
- **Языковая практика**: Изучение Dutch (Nederlands).
- **Синхронизация**: Настроена сквозная синхронизация через Syncthing (`~/.gemini`, `~/.hermes`, `~/Sync`) и Google Drive (`Sync`).

## Global Mission Control (GMC)
Синхронизация OpenClaw, Antigravity и Gemini CLI.

### Статус Агентов:
- **OpenClaw**: Оркестратор (Online).
- **Antigravity**: Системный контроллер (Online). *Является незаменимым участником связки: управляет архитектурой, проводит диагностику, исправляет логические ошибки в кодовой базе и координирует фоновые процессы.*
- **Gemini CLI**: Инженер (Online).

## Архитектура Самовосстановления и Автозапуска
- **Самовосстановление (Agent Complaint System):** При сбое фоновых скриптов или ошибках API Google, агенты пишут жалобу в `AGENTS_COMPLAINTS.md` и отправляют WhatsApp-уведомление Денису с просьбой к Antigravity исправить ошибку. Antigravity автоматически сканирует жалобы и лечит кодовую базу.
- **Автозапуск (Autostart):** На Хромбуке настроены lingering systemd-службы. На телефоне (Termux) автозапуск прописан в `~/.bashrc` для поддержания `sshd` и фоновых агентов.

## Гибридная локально-облачная архитектура (Local Ollama Routing)
- **Локальный роутер ИИ:** Для предотвращения исчерпания облачных токенов и ускорения повседневной работы фоновые агенты на всех устройствах при обычном общении сначала опрашивают локальный API Ollama на порту `11434`.
- **Сеть по Tailscale:** Агенты на телефоне (Termux) и Хромбуке (`penguin`) автоматически перенаправляют свои повседневные запросы на центральный сервер Ollama главного Windows ПК по его Tailscale IP (`100.72.214.118:11434`), который настроен слушать на интерфейсе `0.0.0.0`.
- **Локальная модель:** В качестве основной локальной модели выбрана сверхбыстрая **`gemma2:2b`** от Google. При сложных задачах (команды `!google`, `!run`, зрение/картинки) или недоступности ПК агенты мгновенно и бесшовно переключаются на облачный Gemini.

## История изменений
- **2026-05-17**: Имплементирована гибридная архитектура ИИ (Ollama/Gemma + Gemini) на всех устройствах. Windows ПК настроен как центральный ИИ-сервер с вещанием на `0.0.0.0` по Tailscale. Агенты на мобильных устройствах обновлены для бесшовной локальной работы с моделью `gemma2:2b`.
- **2026-05-17**: Составлено формальное безвоарсхрифт-письмо по налогам. Рассчитана точная личная доля возврата Дениса за AJ 2024 в €2.236,65 (BV €1.425,65 + Werkbonus €281,00 + Kinderkrediet €530,00), которая ушла бывшей жене. Подготовлен черновик в Gmail с 4 официальными pdf-вложениями и сохранен в папку «Черновики» через скрипт `save_draft_bezwaar.py` для согласования и отправки в FOD.
- **2026-05-17**: Добавлен динамический генератор PDF-отчетов по пробегу `generate_pdf_report.py` с офлайн-кэшем расстояний. Реализована система самовосстановления и программного контроля префиксов WhatsApp.
- **2026-05-17**: Обновлен адрес проживания (Engelselei 81 bus 5). Поиск жилья завершен. Добавлен график опеки над сыном (смена по пятницам в 18:00).
- **2026-05-16**: Полное обновление профиля. Исправлена ошибка идентификации пользователя (ранее ошибочно считался "Антоном"). Данные синхронизированы с Google Drive и `MEMORY.md`.

---
*Инструкция для ИИ (Gemini CLI и Antigravity): Всегда проверяй этот файл в начале сессии. Если произошло важное изменение в статусе проекта или целях — обновляй соответствующие разделы.*
