import math
import sys

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Радиус Земли в км
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def process_logs(file_path):
    total_distance = 0
    last_point = None
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if 'ERROR' in line: continue
                parts = line.split('|')
                if len(parts) < 3: continue
                
                try:
                    lat = float(parts[1].strip())
                    lon = float(parts[2].strip())
                    current_point = (lat, lon)
                    
                    if last_point:
                        dist = haversine(last_point[0], last_point[1], lat, lon)
                        # Игнорируем шум (если перемещение меньше 100 метров)
                        if dist > 0.1:
                            total_distance += dist
                    
                    last_point = current_point
                except ValueError:
                    continue
        
        print(f"Пройденное расстояние: {total_distance:.2f} км")
        print(f"Сумма компенсации (0.3450 €/km): {total_distance * 0.345:.2f} €")
    except FileNotFoundError:
        print("Файл логов не найден.")

if __name__ == "__main__":
    log_path = "/data/data/com.termux/files/home/Sync/logs/gps_track.log"
    process_logs(log_path)
