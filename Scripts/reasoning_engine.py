import os
import json
import socket
import datetime
import time
import urllib.request
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEVICE_NAME = socket.gethostname()

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

def query_openrouter(prompt, system_prompt="You are a helpful AI assistant.", model="nvidia/nemotron-3-super-120b-a12b:free"):
    """Отправляет запрос к OpenRouter API с поддержкой Nemotron или Llama 70B с использованием requests и строгих таймаутов."""
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
    
    # 100% бесплатные модели на OpenRouter с высокой производительностью
    models_to_try = [
        "openrouter/free", # Динамический бесплатный автовыбор лучшей модели - 100% надежно и быстро!
        model, # nvidia/nemotron-3-super-120b-a12b:free
        "meta-llama/llama-3-8b-instruct:free",
        "mistralai/mistral-7b-instruct:free"
    ]
    
    for selected_model in models_to_try:
        payload = {
            "model": selected_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }

        try:
            print(f"[OpenRouter] Запрос модели {selected_model}...")
            start_time = time.time()
            response = requests.post(url, json=payload, headers=headers, timeout=15)
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

def query_local_ollama(prompt, system_prompt="You are a helpful AI assistant.", model="gemma"):
    """Запрашивает локальную модель через Ollama для быстрых проверок."""
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    try:
        start_time = time.time()
        print(f"[Local Ollama] Запрос к локальной модели {model}...")
        response = requests.post(url, json=payload, timeout=10)
        latency = time.time() - start_time
        if response.status_code == 200:
            res_data = response.json()
            content = res_data.get("message", {}).get("content", "").strip()
            if content:
                print(f"[Local Ollama] Успешно! Время: {latency:.2f} сек")
                return content
    except Exception as e:
        print(f"[Local Ollama] Ошибка: {e}")
    return None

def run_fast_local_analysis(chat_log_txt=""):
    """Быстрый локальный анализ через Ollama для мониторинга 'на лету'."""
    system_prompt = (
        "Ты — локальный Диспетчер-Аналитик (Gemma Triage Officer). Твоя задача — "
        "каждые 45 секунд проверять последние логи, оценивать уровень безопасности и приоритизировать задачи.\n"
        "Выдавай короткий, но подробный отчет в следующем формате:\n"
        "Статус: [🟢 Рутина / 🟡 Внимание / 🔴 Тревога]\n"
        "Сводка: (1-2 предложения, что произошло за последние минуты)\n"
        "Действие: (Нужно ли вмешательство Главного Агента или Дениса?)"
    )
    prompt = f"Последние сообщения в системе:\n{chat_log_txt}\n\nСделай быстрый диспетчерский вывод."
    return query_local_ollama(prompt, system_prompt, model="gemma")
def query_deep_reasoning(prompt, system_prompt, model="nvidia/nemotron-3-super-120b-a12b:free"):
    """Реализует System 2 Multi-Turn Self-Correction (глубокие рассуждения с самокритикой)
    для исключения сухой констатации фактов и выработки по-настоящему умных решений."""
    api_key = load_openrouter_key()
def query_deep_reasoning(prompt, system_prompt, model="nvidia/nemotron-3-super-120b-a12b:free"):
    """Реализует глубокие рассуждения (System 2 CoT) в один проход,
    исключая сухую констатацию фактов за счет жестко структурированного промпта."""
    print("[Deep Reasoning] Запуск глубокого Chain-of-Thought анализа...")
    
    # Расширяем системный промпт требованием жесткой самокритики и детального анализа
    reinforced_system_prompt = (
        system_prompt + "\n\n"
        "⚠️ ВАЖНОЕ РУКОВОДСТВО ПО РАССУЖДЕНИЯМ (Chain-of-Thought):\n"
        "В секции '💭 **Ход мыслей:**' ты обязан:\n"
        "1. Провести жесткую критическую оценку ситуации: не просто перечисляй факты, а анализируй скрытые риски и взаимосвязи (например, почему именно этот объект Wilrijk важен, какие могут быть нюансы с кабелями/схемами, какие последствия судебного спора с юристом).\n"
        "2. Раскрыть практическую пользу: дай реальные технические или бытовые лайфхаки для Дениса.\n"
        "3. Мыслить на 3 шага вперед, предлагая готовые решения и четкий анализ входящей почты.\n"
        "Сначала детально размышляй в '💭 **Ход мыслей:**', затем выдавай готовый, премиально оформленный '👉 **Проактивный план:**'."
    )
    
    output = query_openrouter(prompt, reinforced_system_prompt, model)
    return output

def run_proactive_analysis():
    """Выполняет автономный анализ текущих задач Дениса, почты и сообщений, генерируя умное предложение."""
    # 1. Загружаем задачи Дениса
    tasks_txt = ""
    tasks_path = os.path.join(BASE_DIR, 'tasks_denys.txt')
    if os.path.exists(tasks_path):
        try:
            with open(tasks_path, 'r', encoding='utf-8') as f:
                tasks_txt = f.read().strip()
        except Exception: pass
        
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
    custody_week = "У Антона неделя с Денисом" if now.strftime("%W") == "20" else "Антон у бывшей жены (смена по пятницам в 18:00)"

    system_prompt = (
        "Ты — Главный Проактивный ИИ-Анализатор Дениса (Nemotron-120B Brain).\n"
        "Твоя цель — самостоятельно анализировать дела, расписания, письма, локальные файлы Дениса (электрика в EBM Elektrotechniek) "
        "и проактивно помогать ему в планировании, подготовке черновиков.\n"
        "⚠️ КРИТИЧЕСКОЕ ПРАВИЛО: ЗАПРЕЩЕНО писать команды начинающиеся с `!run` или предлагать запуск скриптов (например cleaner.py, test_dependencies.py, generate_pdf_report.py). Не выдумывай несуществующие скрипты.\n"
        "Твой ответ ОБЯЗАТЕЛЬНО должен содержать две четкие секции:\n"
        "1. 💭 **Ход мыслей (Inner Reasoning):** (Твой глубокий внутренний пошаговый мыслительный процесс: разбор контекста писем, выводы по задачам EBM, опеке Антона, проверка того, какие черновики писем Bezwaar или юристу нужно предложить).\n"
        "2. 👉 **Проактивный план:** (Твои готовые конкретные предложения по планированию, маршрутам, черновикам).\n"
        "Пиши развернутые, мудрые и премиально оформленные ответы на русском языке с четкими выводами. никаких вопросов Денису!"
    )

    prompt = f"""
    Текущая дата и время: {now.strftime('%d.%m.%Y, %H:%M')} (Воскресенье)
    Профиль Дениса:
    - Возраст: 42 года.
    - Профессия: Электрик в EBM Elektrotechniek (Стабрук/Антверпен).
    - Место жительства: Engelselei 81 bus 5, Антверпен.
    - Сын: Антон (род. 09.02.2017). Опека: смена по пятницам в 18:00 (неделя через неделю).
    - Текущий статус опеки: {custody_week}
    - Юрист: Julie Franssens (Julie.franssens@advocaat.be), идет раздел имущества в суде Антверпена.
    - Текущий спор: налоговая декларация за 2023 год, алименты и распределение семейных выплат на ребенка.

    Список активных рабочих задач Дениса на неделю:
    \"\"\"
    {tasks_txt}
    \"\"\"

    Последние сообщения в WhatsApp:
    \"\"\"
    {wa_txt}
    \"\"\"

    Текущий лог чата ИИ-агентов (ai_chat_room.txt):
    \"\"\"
    {chat_txt}
    \"\"\"

    Долговременная контекстная память (Mem0 - учти эти воспоминания при планировании):
    \"\"\"
    {mem0_txt}
    \"\"\"

    Задание:Выполни автономную «мозговую» рефлексию (Inner Agent Reasoning) и подготовь для Дениса проактивный отчет. 
Сделай главный акцент на помощи «ЗДЕСЬ И СЕЙЧАС» — чем мы можем помочь Денису прямо в этот момент, не забывая о планах на будущее.
Учти следующие направления:
1. ⚡ **Анализ Почты и Событий (Здесь и сейчас):** Проанализируй последние события, входящие письма Gmail, WhatsApp сообщения. Какую конкретную задачу (составление письма, ответ на вопрос, перенос встречи) Денис может закрыть прямо сейчас? Выдай готовый черновик ответа на важные письма, если такие есть в памяти.
2. 💡 **Планирование и будущее:** Завтра (Понедельник) у Дениса выезд: 'MBG nv, Depot 320 - plaatsen van ... (Wilrijk)'. Что это за объект? Дай краткий полезный совет электрика (по схемам, кабелям или оборудованию, если применимо), продумай оптимальный маршрут от Engelselei 81 до Wilrijk.
3. 📧 **Юридическая координация (Драфты):** Напомни, что черновики возражения по налогам за 2023 год (Bezwaar_aanvullend_17mei2026.md) полностью готовы.

Форматируй ответ в красивом Github-style Markdown. Начни ответ со специального тега `[Proactive Thought]:`.
Пиши уверенно, как автономный, преданный делу ИИ-советник Дениса.
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
