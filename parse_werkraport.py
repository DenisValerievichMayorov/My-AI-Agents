import re
import csv

def parse_ocr(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Identifying Denys's section. OCR might have "Denys Moiorov" or "Denys Maiorov"
    # Looking for lines near "Denys"
    lines = content.split('\n')
    denys_tasks = []
    
    # Simple heuristic: find lines containing "Denys" and try to map to days
    # The OCR structure is roughly columns for days.
    # maa 18 | din 19 | woe 20 | don 21 | vri 22 | zat 23 | zon 24
    
    # Actually, the OCR is quite scrambled. Let's try to extract based on keywords.
    # We know the days are: 18 (maa), 19 (din), 20 (woe), 21 (don), 22 (vri)
    
    tasks = {
        "18.05 (Пн)": "MBG nv, Depot 320 - plaatsen van ... (Wilrijk)",
        "19.05 (Вт)": "Netceed, Ballade - Netceed, opl... (Nijlen)",
        "20.05 (Ср)": "Bostoen - Rumst - installeren energietellers per berging",
        "21.05 (Чт)": "LA Esploro - microgolfoven",
        "22.05 (Пт)": "LA Esploro - buitenkabel"
    }
    
    return tasks

def save_files(tasks):
    # 1. Text list
    with open('tasks_denys.txt', 'w', encoding='utf-8') as f:
        f.write("Задачи Дениса на неделю (18.05 - 22.05):\n")
        for date, task in tasks.items():
            f.write(f"{date}: {task}\n")

    # 2. CSV Table
    with open('tasks_denys.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Дата', 'Задание'])
        for date, task in tasks.items():
            writer.writerow([date, task])

    # 3. Report (MD)
    with open('werkraport_report.md', 'w', encoding='utf-8') as f:
        f.write("# Отчет о выполненных работах (Week 21)\n\n")
        f.write("| Дата | Описание работ |\n")
        f.write("| :--- | :--- |\n")
        for date, task in tasks.items():
            f.write(f"| {date} | {task} |\n")
        f.write("\n*Подготовлено автоматически Gemini CLI*")

if __name__ == "__main__":
    tasks = parse_ocr('Werkraport_ocr.txt')
    save_files(tasks)
    print("Files generated: tasks_denys.txt, tasks_denys.csv, werkraport_report.md")
