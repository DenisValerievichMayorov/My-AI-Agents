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
    "rumst": (51.0772, 4.4239),
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
        with open(INPUT_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                desc = row['Задание']
                loc = "Antwerpen"
                if '(' in desc and ')' in desc:
                    loc = desc[desc.rfind('(')+1:desc.rfind(')')]
                elif '-' in desc:
                    parts = desc.split('-')
                    if len(parts) > 1:
                        loc = parts[-1].strip().split(' ')[0]
                
                tasks.append({
                    "date": row['Дата'],
                    "desc": desc,
                    "loc": loc
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
        if FONT_PATH:
            if FONT_NAME not in self.fonts:
                self.add_font(FONT_NAME, "", FONT_PATH)
            self.set_font(FONT_NAME, size=12)
        else:
            self.set_font("Arial", size=12)
        
        self.cell(0, 10, "WORK REPORT - EBM ELEKTROTECHNIEK", new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font(FONT_NAME, size=8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

def calculate_mileage(dest):
    dest_key = dest.lower().strip()
    home_coords = COORDINATES_CACHE["engelselei 81, 2140 antwerpen, belgium"]
    
    # Try looking up coordinates in static cache first (100% offline-ready, 0ms latency)
    target_coords = None
    for key, coords in COORDINATES_CACHE.items():
        if key in dest_key or dest_key in key:
            target_coords = coords
            break
            
    if target_coords:
        dist = geodesic(home_coords, target_coords).km
        return round(dist * 1.3 * 2, 2)
        
    # Fallback to online geocoder if not in cache
    geolocator = Nominatim(user_agent="gemini_cli_reporter")
    try:
        time.sleep(1)
        home = geolocator.geocode(HOME_ADDRESS)
        target = geolocator.geocode(dest + ", Belgium")
        if home and target:
            dist = geodesic((home.latitude, home.longitude), (target.latitude, target.longitude)).km
            return round(dist * 1.3 * 2, 2)
    except Exception:
        pass
    return 0

def generate_pdf(tasks=None):
    if not tasks:
        tasks = load_tasks_from_csv()
    if not tasks:
        tasks = SAMPLE_TASKS

    pdf = PDFReport()
    pdf.add_page()
    
    if FONT_PATH:
        if FONT_NAME not in pdf.fonts:
            pdf.add_font(FONT_NAME, "", FONT_PATH)
        pdf.set_font(FONT_NAME, size=10)
    else:
        pdf.set_font("Arial", size=10)

    pdf.set_fill_color(200, 220, 255)
    pdf.cell(30, 10, "Date", border=1, fill=True)
    pdf.cell(110, 10, "Description", border=1, fill=True)
    pdf.cell(30, 10, "KM (Return)", border=1, fill=True)
    pdf.ln()

    total_km = 0
    for task in tasks:
        km = calculate_mileage(task['loc'])
        total_km += km
        
        pdf.cell(30, 10, task['date'], border=1)
        x = pdf.get_x()
        y = pdf.get_y()
        pdf.multi_cell(110, 10, task['desc'], border=1)
        pdf.set_xy(x + 110, y)
        pdf.cell(30, 10, str(km), border=1)
        pdf.ln()

    pdf.ln(5)
    pdf.set_font(FONT_NAME, size=12)
    pdf.cell(0, 10, f"TOTAL KM: {round(total_km, 2)}", new_x="LMARGIN", new_y="NEXT", align="R")
    
    # Ensure parent output folder exists
    parent_dir = os.path.dirname(OUTPUT_PDF)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir)
        
    pdf.output(OUTPUT_PDF)
    print(f"PDF saved successfully as {OUTPUT_PDF}")

if __name__ == "__main__":
    generate_pdf()
