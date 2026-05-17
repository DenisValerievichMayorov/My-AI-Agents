import os
import json
import csv
import time
from fpdf import FPDF
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# --- Configuration ---
HOME_ADDRESS = "Engelselei 81, 2140 Antwerpen, Belgium"
OUTPUT_PDF = "Werkraports/Werkraport_Report.pdf"
INPUT_CSV = "tasks_denys.csv"

# --- Static Coordinates Cache (for offline instant computation) ---
COORDINATES_CACHE = {
    "engelselei 81, 2140 antwerpen, belgium": (51.21361, 4.43956),
    "wilrijk": (51.1685, 4.3989),
    "nijlen": (51.1578, 4.6853),
    "gent": (51.0374, 3.6931),
    "rumst": (51.0924, 4.4079),
    "la esploro": (51.0259, 4.4776),
    "antwerpen": (51.21361, 4.43956)
}

# --- Dynamic Font Resolution ---
def get_system_font():
    candidates = [
        "/system/fonts/Roboto-Regular.ttf", # Android/Termux
        "C:\\Windows\\Fonts\\arial.ttf",     # Windows
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", # Debian/Chromebook
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", # Debian/Chromebook
        "/usr/share/fonts/chromeos/roboto/Roboto-Regular.ttf" # ChromeOS alternate
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None

FONT_PATH = get_system_font()
FONT_NAME = "RobotoCustom" if FONT_PATH else "Arial"

def load_tasks_from_csv():
    tasks = []
    if os.path.exists(INPUT_CSV):
        # Используем utf-8-sig для корректной обработки BOM в Windows
        with open(INPUT_CSV, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                desc = row['Задание']
                desc_lower = desc.lower()
                
                # Приоритет поиска локаций
                found_loc = "antwerpen"
                for key in COORDINATES_CACHE.keys():
                    if key in desc_lower and key != "engelselei 81, 2140 antwerpen, belgium" and key != "antwerpen":
                        found_loc = key
                        break
                
                tasks.append({
                    "date": row['Дата'],
                    "desc": desc,
                    "loc": found_loc
                })
    return tasks

SAMPLE_TASKS = [
    {"date": "18.05 (Пн)", "desc": "MBG nv, Depot 320 - Wilrijk", "loc": "Wilrijk"},
    {"date": "19.05 (Вт)", "desc": "Netceed, Ballade - Nijlen", "loc": "Nijlen"},
    {"date": "20.05 (Ср)", "desc": "Bostoen - Rumst", "loc": "Rumst"},
    {"date": "21.05 (Чт)", "desc": "LA Esploro - Antwerpen", "loc": "Antwerpen"},
    {"date": "22.05 (Пт)", "desc": "LA Esploro - Antwerpen", "loc": "Antwerpen"}
]

class PDFReport(FPDF):
    def header(self):
        if False: # Forced Arial
            if FONT_NAME not in self.fonts:
                self.add_font(FONT_NAME, "", FONT_PATH)
            self.set_font(FONT_NAME, size=12)
        else:
            self.set_font("Arial", size=12)
        
        self.cell(0, 10, "WORK REPORT - EBM ELEKTROTECHNIEK", 0, 1, "C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", size=8) # Changed from FONT_NAME to Arial for safety
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

def calculate_mileage(dest):
    dest_key = dest.lower().strip()
    home_coords = COORDINATES_CACHE["engelselei 81, 2140 antwerpen, belgium"]
    
    # Принудительная проверка по ключам в кэше
    for key, coords in COORDINATES_CACHE.items():
        if key in dest_key:
            if key == "antwerpen" or key == "engelselei 81, 2140 antwerpen, belgium":
                return 10.0
            dist = geodesic(home_coords, coords).km
            return round(dist * 1.3 * 2, 2)
            
    return 10.0 # Default fallback

def generate_pdf(tasks=None):
    if not tasks:
        tasks = load_tasks_from_csv()
    if not tasks:
        tasks = SAMPLE_TASKS

    pdf = PDFReport()
    pdf.add_font("Arial", "", "C:/Windows/Fonts/arial.ttf", uni=True)
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    pdf.set_fill_color(200, 220, 255)
    pdf.cell(30, 10, "Date", border=1, fill=True)
    pdf.cell(110, 10, "Description", border=1, fill=True)
    pdf.cell(30, 10, "KM (Return)", border=1, fill=True)
    pdf.ln()

    # ... (код функции)
    total_km = 0
    for task in tasks:
        # ПРЯМОЙ РАСЧЕТ В ЦИКЛЕ
        dest = task['loc']
        km = 0
        if dest in COORDINATES_CACHE and dest != "antwerpen" and dest != "engelselei 81, 2140 antwerpen, belgium":
            dist = geodesic(HOME_ADDRESS, COORDINATES_CACHE[dest]).km
            km = round(dist * 1.3 * 2, 2)
        else:
            km = 10.0
        total_km += km
        
        pdf.cell(30, 10, task['date'], border=1)
        # ... (остальной код)

    pdf.ln(5)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"TOTAL KM: {round(total_km, 2)}", 0, 1, "R")
    
    # Ensure parent output folder exists
    parent_dir = os.path.dirname(OUTPUT_PDF)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir)
        
    pdf.output(OUTPUT_PDF)
    print(f"PDF saved successfully as {OUTPUT_PDF}")

if __name__ == "__main__":
    generate_pdf()
