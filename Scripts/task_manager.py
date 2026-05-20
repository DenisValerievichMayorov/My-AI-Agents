import os
import json
import datetime

TASKS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tasks_agent.json')

def default_tasks():
    return {"tasks": [], "next_id": 1}

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        data = default_tasks()
        save_tasks(data)
        return data
    try:
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default_tasks()

def save_tasks(data):
    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_all():
    data = load_tasks()
    return data.get("tasks", [])

def get_active():
    data = load_tasks()
    return [t for t in data.get("tasks", []) if not t.get("done")]

def add(text):
    data = load_tasks()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    task = {"id": data["next_id"], "text": text, "done": False, "created": now}
    data["tasks"].insert(0, task)
    data["next_id"] += 1
    save_tasks(data)
    return task

def update(task_id, text=None, done=None):
    data = load_tasks()
    for t in data["tasks"]:
        if t["id"] == task_id:
            if text is not None:
                t["text"] = text
            if done is not None:
                t["done"] = done
            save_tasks(data)
            return t
    return None

def delete(task_id):
    data = load_tasks()
    before = len(data["tasks"])
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    if len(data["tasks"]) < before:
        save_tasks(data)
        return True
    return False

def reorder(task_ids):
    data = load_tasks()
    tasks_map = {t["id"]: t for t in data["tasks"]}
    new_order = []
    for tid in task_ids:
        if tid in tasks_map:
            new_order.append(tasks_map[tid])
    remaining = [t for t in data["tasks"] if t["id"] not in task_ids]
    data["tasks"] = new_order + remaining
    save_tasks(data)

def format_tasks_for_prompt():
    tasks = get_active()
    if not tasks:
        return "Список задач пуст. Ты можешь предложить Денису добавить новую задачу."
    lines = ["Текущие активные задачи (работай ТОЛЬКО по ним):"]
    for t in tasks:
        lines.append(f"  [{t['id']}] {t['text']}")
    lines.append("")
    lines.append("⚠️ ПРАВИЛО: Не выдумывай задачи которых нет в списке.")
    lines.append("Если хочешь предложить новую задачу — напиши '!taskadd: <текст>' и дождись когда Денис её добавит.")
    return "\n".join(lines)
