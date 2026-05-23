import os
import json
import datetime
import subprocess
import re

# Конфигурация путей
SYNC_DIR = "/data/data/com.termux/files/home/Sync"
EMAILS_DIR = os.path.join(SYNC_DIR, "Data", "emails")
REPORTS_DIR = os.path.join(SYNC_DIR, "Reports", "email_summaries")
MEMORY_FILE = "/data/data/com.termux/files/home/.gemini/tmp/home/memory/MEMORY.md" # Согласно сессионному контексту, но проверим наличие
LOG_FILE = os.path.join(SYNC_DIR, "Logs", "email_parsing.log")
READ_PDF_SCRIPT = os.path.join(SYNC_DIR, "Scripts", "read_pdf.py")

# Попробуем найти правильный путь к MEMORY.md
if not os.path.exists(os.path.dirname(MEMORY_FILE)):
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    if not os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            f.write("# Project Memory\n")

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(message)

def get_pdf_text(path):
    try:
        result = subprocess.run(["python", READ_PDF_SCRIPT, path], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        log(f"Error reading PDF {path}: {e}")
        return ""

def ask_llm(prompt):
    # Используем системный подход: вызываем ollama или через curl к API если доступно
    # Для упрощения в этом скрипте, мы подготовим prompt для суммаризации
    # Но так как я агент, я могу выполнить это действие в следующем шаге
    # Поэтому этот скрипт будет просто подготавливать данные для меня
    return f"[LLM Summary Placeholder for prompt: {prompt[:50]}...]"

def process_emails():
    emails = [f for f in os.listdir(EMAILS_DIR) if f.endswith(".json")]
    log(f"Found {len(emails)} emails to parse.")
    
    for email_file in emails:
        with open(os.path.join(EMAILS_DIR, email_file), "r", encoding="utf-8") as f:
            data = json.load(f)
        
        msg_id = data['id']
        report_path = os.path.join(REPORTS_DIR, f"{msg_id}.md")
        
        if os.path.exists(report_path):
            continue
            
        full_text = f"Subject: {data['subject']}\nFrom: {data['from']}\nDate: {data['date']}\n\n{data['body']}\n"
        
        for att in data.get('attachments', []):
            if att['filename'].lower().endswith('.pdf'):
                log(f"Extracting text from attachment: {att['filename']}")
                pdf_text = get_pdf_text(att['path'])
                full_text += f"\n--- Attachment: {att['filename']} ---\n{pdf_text}\n"

        # В реальном сценарии здесь был бы вызов к LLM API
        # Но так как я (Gemini) управляю процессом, я соберу наиболее важные письма сам
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Email Summary: {data['subject']}\n\n")
            f.write(f"**From:** {data['from']}\n")
            f.write(f"**Date:** {data['date']}\n\n")
            f.write("## Content\n")
            f.write(data['body'][:2000] + ("..." if len(data['body']) > 2000 else ""))
            if data.get('attachments'):
                f.write("\n\n## Attachments\n")
                for att in data['attachments']:
                    f.write(f"- {att['filename']}\n")
        
        log(f"Processed email: {data['subject']}")

if __name__ == "__main__":
    os.makedirs(REPORTS_DIR, exist_ok=True)
    process_emails()
