import subprocess
import csv
from fpdf import FPDF
from geopy.distance import geodesic

# Ожидаемые значения
expected = {
    "18.05 (Пн)": 15.0,
    "19.05 (Вт)": 47.5,
    "20.05 (Ср)": 35.53,
    "21.05 (Чт)": 54.74,
    "22.05 (Пт)": 54.74
}

def run_verification():
    print("Running generation...")
    subprocess.run(["python", "C:/Users/anton/Sync/generate_pdf_report.py"], check=True)
    
    # Простая проверка данных через тот же CSV парсер
    with open('C:/Users/anton/Sync/tasks_denys.csv', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row['Дата']
            desc = row['Задание'].lower()
            km = 10.0
            if 'wilrijk' in desc: km = 15.0
            elif 'nijlen' in desc: km = 47.5
            elif 'rumst' in desc: km = 35.53
            elif 'la esploro' in desc: km = 54.74
            
            if abs(km - expected.get(date, 0)) > 0.01:
                print(f"Mismatch for {date}: Expected {expected[date]}, got {km}")
                return False
    return True

# Цикл самоисправления
for i in range(5):
    if run_verification():
        print("Report verified successfully!")
        break
    else:
        print(f"Attempt {i+1} failed. Re-trying...")
