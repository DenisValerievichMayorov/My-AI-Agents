import os
import json
import socket
import datetime
import time
import urllib.request
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEVICE_NAME = socket.gethostname()

# Local Ollama removed 2026-08-02
LOCAL_LLM_ENABLED = False

OPENROUTER_HEAVY_ENABLED = os.environ.get("GMC_OPENROUTER_HEAVY", "").lower() in ("1", "true", "yes", "on")
DEFAULT_MODEL = "google/gemma-4-31b-it:free"
OPENROUTER_TIMEOUT = float(os.environ.get("GMC_OPENROUTER_TIMEOUT", "25"))
HEAVY_MODEL_TIMEOUT = float(os.environ.get("GMC_HEAVY_MODEL_TIMEOUT", "90"))

def openrouter_model_timeout(model_name):
    return HEAVY_MODEL_TIMEOUT if (model_name and "deepseek" not in model_name.lower()) else OPENROUTER_TIMEOUT

def build_openrouter_models(preferred_model=None, prefer_nemotron=False):
    models = []
    if prefer_nemotron or (preferred_model and "nemotron" in preferred_model.lower()):
        models.append(DEFAULT_MODEL)
    models.append("openrouter/free")
    if preferred_model and preferred_model not in models:
        models.append(preferred_model)
    return list(dict.fromkeys(models))

def load_openrouter_key():
    """Загружает OpenRouter API ключ из .hermes/.env (сначала локальный, затем системный)."""
    paths = [
        os.path.join(BASE_DIR, '.hermes', '.env'),
        os.path.expanduser("~/.hermes/.env"),
        "C:/Users/anton/.hermes/.env"
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('OPENROUTER_API_KEY='):
                            key = line.split('OPENROUTER_API_KEY=')[1].strip()
                            if key and key != '[REDACTED_KEY]':
                                return key
            except Exception:
                pass
    return None

def query_openrouter(prompt, system_prompt="You are a helpful AI assistant.", model=DEFAULT_MODEL):
    """OpenRouter: Nemotron первым (если heavy/явно), иначе openrouter/free как резерв."""
    api_key = load_openrouter_key()
    if not api_key:
        print("[OpenRouter] API ключ не найден в конфигурациях .hermes/.env")
        return None
        
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/antigravity/gmc",
        "X-Title": "GMC Proactive Brain"
    }

    prefer_nemotron = OPENROUTER_HEAVY_ENABLED or "nemotron" in (model or "").lower()
    models_to_try = build_openrouter_models(model, prefer_nemotron=prefer_nemotron)
    
    for selected_model in models_to_try:
        payload = {
            "model": selected_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }

        is_deepseek = "deepseek" in selected_model.lower()
        if is_deepseek:
            payload["reasoning"] = {"effort": "high"}

        try:
            timeout = openrouter_model_timeout(selected_model)
            print(f"[OpenRouter] Запрос модели {selected_model} (timeout {timeout:.0f}s)...")
            start_time = time.time()
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            latency = time.time() - start_time
            if response.status_code == 200:
                res_data = response.json()
                choices = res_data.get('choices', [])
                if choices:
                    msg = choices[0].get('message', {})
                    content = msg.get('content') if msg else None
                    if content:
                        content = content.strip()
                        speed_msg = f"ОТЛИЧНАЯ СКОРОСТЬ" if latency < 5 else f"МЕДЛЕННО"
                        print(f"[OpenRouter] Успешный ответ от модели: {selected_model}! Время: {latency:.2f} сек ({speed_msg})")
                        return content
            else:
                print(f"[OpenRouter] Ошибка {selected_model}: HTTP {response.status_code} (Время: {latency:.2f} сек) - {response.text}")
        except Exception as e:
            print(f"[OpenRouter] Ошибка при запросе {selected_model}: {e}")

    return None

def query_local_ollama(prompt, system_prompt="You are a helpful AI assistant.", model=None):
    """Deprecated: local Ollama removed. Always returns None."""
    print("[Local Ollama] disabled (removed 2026-08-02) — use OpenRouter")
    return None


def run_fast_local_analysis(chat_log_txt=""):
    """Fast triage via OpenRouter (local Ollama removed)."""
    system_prompt = (
        "Ты — Диспетчер-Аналитик (быстрый triage). Твоя задача — "
        "проверить последние логи и выдать чёткий вердикт.\n\n"
        "Формат ответа (строго):\n"
        "Статус: [🟢 Рутина / 🟡 Внимание / 🔴 Тревога]\n"
        "Сводка: (1 предложение, суть)\n"
        "Действие: (Нужно ли вмешательство? Если нет — «Не требуется»)"
    )
    prompt = (
        "Последние сообщения в системе:\n"
        + str(chat_log_txt)
        + "\n\nСделай быстрый диспетчерский вывод."
    )
    return query_openrouter(prompt, system_prompt, model=DEFAULT_MODEL)


def query_deep_reasoning(prompt, system_prompt, model=DEFAULT_MODEL):
    """Реализует глубокие рассуждения (System 2 CoT) в один проход,
    исключая сухую констатацию фактов за счет жестко структурированного промпта."""
    print("[Deep Reasoning] Запуск глубокого Chain-of-Thought анализа...")
    
    # Расширяем системный промпт структурированным Chain-of-Thought с самокритикой
    reinforced_system_prompt = (
        system_prompt + "\n\n"
        "⚠️ ПРОДВИНУТЫЙ ПРОТОКОЛ РАССУЖДЕНИЙ (System 2 Chain-of-Thought):\n"
        "Ты обязан следовать строгой структуре мышления:\n\n"
        "### Шаг 1: Рекогносцировка (сбор данных)\n"
        "- Какие факты известны? Что нового появилось?\n"
        "- Какие задачи активны, какие заблокированы?\n\n"
        "### Шаг 2: Глубокий анализ\n"
        "- Найди скрытые взаимосвязи между фактами.\n"
        "- Оцени риски: что пойдёт не так? Что можно оптимизировать?\n"
        "- Проверь противоречия: не устарели ли данные?\n\n"
        "### Шаг 3: Самокритика (Self-Critique)\n"
        "- Перепроверь свой анализ: не упустил ли ты что-то?\n"
        "- Есть ли альтернативные интерпретации?\n"
        "- Какие данные нужны для точного решения?\n\n"
        "### Шаг 4: Проактивный план\n"
        "- Конкретные, измеримые действия.\n"
        "- Приоритет: что сделать прямо сейчас vs отложить.\n"
        "- Если нужна новая задача — предложи через !taskadd:\n\n"
        "Формат ответа:\n"
        "1. 💭 **Ход мыслей:** (шаги 1-3)\n"
        "2. 👉 **Проактивный план:** (шаг 4, 3-5 пунктов)\n"
        "Запрещено: пустые обобщения, вопросы Денису, повтор старых советов."
    )
    
    return query_openrouter(prompt, reinforced_system_prompt, model=model)

def run_proactive_analysis():
    """Выполняет автономный анализ текущих задач Дениса, почты и сообщений, генерируя умное предложение."""
    # 1. Загружаем задачи из task_manager (только активные, не выполненные)
    try:
        import task_manager
        tasks_txt = task_manager.format_tasks_for_prompt()
    except Exception:
        tasks_txt = "Список задач не загружен."
        
    # 2. Загружаем переписку чат-рума для контекста
    chat_txt = ""
    chat_path = os.path.join(BASE_DIR, 'ai_chat_room.txt')
    if os.path.exists(chat_path):
        try:
            with open(chat_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                chat_txt = "".join(lines[-15:])
        except Exception: pass
        
    # 3. Загружаем историю WhatsApp
    wa_txt = ""
    wa_path = os.path.join(BASE_DIR, 'whatsapp_messages.txt')
    if os.path.exists(wa_path):
        try:
            with open(wa_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                wa_txt = "".join(lines[-15:])
        except Exception: pass

    # 3.5 Загружаем долговременную память (Mem0)
    mem0_txt = ""
    try:
        from mem0 import MemoryClient
        if 'MEM0_API_KEY' not in os.environ:
            os.environ['MEM0_API_KEY'] = 'm0-FNdckglmWWITMYsm2J4MjQEmuW9zFGD5bmLN3vKp'
        client = MemoryClient()
        res = client.search('Последние важные письма, задачи, переписка и события', filters={'user_id': 'denis'})
        if res and 'results' in res:
            memories = [f"- {m['memory']}" for m in res['results']]
            mem0_txt = "\n".join(memories)
    except Exception as e:
        print(f"[Mem0] Ошибка загрузки памяти: {e}")

    # 4. Формируем глубокий контекстный промпт
    now = datetime.datetime.now()
    weekdays = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    day_name = weekdays[now.weekday()]

    system_prompt = (
        "Ты — Главный Проактивный ИИ-Стратег Дениса.\n"
        "Твоя задача — работать ТОЛЬКО по задачам из списка ниже.\n"
        "⚠️ КРИТИЧЕСКОЕ ПРАВИЛО: Ты НЕ имеешь права выдумывать, предлагать или обсуждать задачи, которых нет в списке.\n"
        "Если считаешь что нужна новая задача — напиши '!taskadd: <текст задачи>' чтобы Денис сам решил.\n"
        "Никогда не предлагай запуск скриптов (!run, !google) без явной задачи в списке.\n\n"
        "### Твой процесс мышления:\n"
        "1. **Контекст**: Сверь текущие задачи с новыми сообщениями (WhatsApp, чат, Mem0). Что изменилось?\n"
        "2. **Анализ**: По каждой задаче оцени: статус, блокеры, следующий шаг. Приоритизируй по срочности.\n"
        "3. **Самопроверка**: Не дублируешь ли ты предыдущий совет? Не упустил ли деталь?\n"
        "4. **План**: Конкретные действия по задачам из списка.\n\n"
        "Формат ответа:\n"
        "1. 💭 **Ход мыслей:** (твой анализ, шаги 1-3)\n"
        "2. 👉 **Проактивный план:** (шаг 4). Если в списке пусто: «Нет задач. Ожидаю. !taskadd: ...»\n"
        "Пиши на русском. Максимум 10-15 строк. Никаких вопросов Денису."
    )

    prompt = f"""
    Дата и время: {now.strftime('%d.%m.%Y, %H:%M')} ({day_name})

    {tasks_txt}

    WhatsApp:
    \"\"\"
    {wa_txt}
    \"\"\"

    Чат:
    \"\"\"
    {chat_txt}
    \"\"\"

    Память (Mem0):
    \"\"\"
    {mem0_txt}
    \"\"\"

    Задание: Работай ТОЛЬКО по задачам из списка выше. 
    Если в списке пусто — напиши кратко «Нет задач. Ожидаю.» и если есть идея — предложи через !taskadd.
    Запрещено выдумывать задачи. Запрещено повторять старые советы.
    Формат: Github Markdown. Тег `[Proactive Thought]:`. Не более 10-15 строк.
"""
    
    return query_deep_reasoning(prompt, system_prompt)

if __name__ == "__main__":
    print("Testing Proactive Brain...")
    res = run_proactive_analysis()
    if res:
        print("\n=== GENERATED REPORT ===\n")
        print(res)
    else:
        print("Failed to query OpenRouter API.")
