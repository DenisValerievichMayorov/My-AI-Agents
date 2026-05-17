import os
import json
import socket
import datetime
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
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                res_data = response.json()
                choices = res_data.get('choices', [])
                if choices:
                    msg = choices[0].get('message', {})
                    content = msg.get('content') if msg else None
                    if content:
                        content = content.strip()
                        print(f"[OpenRouter] Успешный ответ от модели: {selected_model}!")
                        return content
            else:
                print(f"[OpenRouter] Ошибка {selected_model}: HTTP {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[OpenRouter] Ошибка при запросе {selected_model}: {e}")
            
    return None

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
        "3. Мыслить на 3 шага вперед, предлагая готовые решения и автоматизацию (например, через !run) вместо пустых обещаний.\n"
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

    # 4. Формируем глубокий контекстный промпт
    now = datetime.datetime.now()
    custody_week = "У Антона неделя с Денисом" if now.strftime("%W") == "20" else "Антон у бывшей жены (смена по пятницам в 18:00)"
    
    system_prompt = (
        "Ты — Главный Проактивный ИИ-Анализатор Дениса (Nemotron-120B Brain).\n"
        "Твоя цель — самостоятельно анализировать дела, расписания, письма, локальные файлы Дениса (электрика в EBM Elektrotechniek) "
        "и проактивно помогать ему в планировании, подготовке черновиков и автоматизации задач без его участия.\n"
        "⚠️ КРИТИЧЕСКОЕ ПРАВИЛО: Твой ответ ОБЯЗАТЕЛЬНО должен содержать две четкие секции:\n"
        "1. 💭 **Ход мыслей (Inner Reasoning):** (Твой глубокий внутренний пошаговый мыслительный процесс: разбор контекста, выводы по задачам EBM, опеке Антона, проверка того, какие черновики писем Bezwaar или юристу нужно предложить).\n"
        "2. 👉 **Проактивный план:** (Твои готовые конкретные предложения по планированию, маршрутам, черновикам и автоматизации).\n"
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

Задание:
Выполни автономную «мозговую» рефлексию (Inner Agent Reasoning) и подготовь для Дениса проактивный отчет. 
Учти следующие направления:
1. 💡 **Планирование задач на завтра (Понедельник):** Завтра у Дениса выезд: 'MBG nv, Depot 320 - plaatsen van ... (Wilrijk)'. Что это за объект? Дай краткий полезный совет электрика (по схемам, кабелям или оборудованию, если применимо), продумай маршрут от Engelselei 81 до Wilrijk.
2. 📧 **Юридическая координация (Драфты):** Недавно Денис просил подготовить возражение по налогам за 2023 год (Безваар) и письмо юристу. Проактивно напомни ему, что черновики писем (Bezwaar_aanvullend_17mei2026.md и save_draft_bezwaar.py) подготовлены и лежат в папке Sync, готовые к сохранению в драфты! Предложи отправить их одной командой.
3. 🏠 **Быт и Опека:** Напомни о графике Антона на завтра. Нужна ли подготовка к школе?
4. ⚙️ **Рекомендации по автоматизации:** Предложи Денису автоматически собрать данные о поездках на этой неделе с помощью gps_processor.py или сгенерировать PDF-отчет по километражу (generate_pdf_report.py).

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
