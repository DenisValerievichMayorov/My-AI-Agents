import os
import glob
import psutil
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_file_size_mb(path):
    try:
        return os.path.getsize(path) / (1024 * 1024)
    except Exception:
        return 0

def clean_sync_conflicts():
    """Находит и удаляет файлы конфликтов Syncthing (*.sync-conflict-*) и временные файлы (~syncthing~*)."""
    print("[Cleaner] Поиск конфликтов и мусора Syncthing...")
    deleted_count = 0
    bytes_saved = 0
    
    # 1. Поиск *.sync-conflict-*
    patterns = [
        os.path.join(BASE_DIR, "**", "*.sync-conflict-*"),
        os.path.join(BASE_DIR, "**", "~syncthing~*")
    ]
    
    for pattern in patterns:
        for filepath in glob.glob(pattern, recursive=True):
            try:
                size = os.path.getsize(filepath)
                os.remove(filepath)
                deleted_count += 1
                bytes_saved += size
                print(f"[Cleaner] Удален мусорный файл: {os.path.basename(filepath)} ({size} bytes)")
            except Exception as e:
                print(f"[Cleaner] Не удалось удалить {filepath}: {e}")
                
    print(f"[Cleaner] Очистка мусора завершена. Удалено файлов: {deleted_count}. Освобождено: {bytes_saved / 1024:.2f} KB")
    return deleted_count, bytes_saved

def truncate_logs():
    """Ротирует и урезает лог-файлы, если они превышают 2 МБ, оставляя только последние 1000 строк."""
    print("[Cleaner] Проверка размеров лог-файлов...")
    log_files = [
        os.path.join(BASE_DIR, "agent.log"),
        os.path.join(BASE_DIR, "heartbeat.log"),
        os.path.join(BASE_DIR, "whatsapp_bridge.log"),
        os.path.join(BASE_DIR, "test_bridge_debug.log"),
        os.path.join(BASE_DIR, "test_bridge.log")
    ]
    
    # Добавляем все файлы .log в каталоге logs
    logs_dir = os.path.join(BASE_DIR, "logs")
    if os.path.exists(logs_dir):
        for f in os.listdir(logs_dir):
            if f.endswith(".log"):
                log_files.append(os.path.join(logs_dir, f))
                
    for log_path in log_files:
        if os.path.exists(log_path):
            size_mb = get_file_size_mb(log_path)
            if size_mb > 2.0:
                print(f"[Cleaner] Лог {os.path.basename(log_path)} слишком большой ({size_mb:.2f} MB). Урезаю...")
                try:
                    # Читаем последние 1000 строк
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    keep_lines = lines[-1000:]
                    # Перезаписываем файл
                    with open(log_path, 'w', encoding='utf-8') as f:
                        f.writelines(keep_lines)
                    new_size = get_file_size_mb(log_path)
                    print(f"[Cleaner] Лог {os.path.basename(log_path)} успешно урезан. Новый размер: {new_size:.4f} MB")
                except Exception as e:
                    print(f"[Cleaner] Не удалось урезать лог {log_path}: {e}")

def kill_zombie_chromes():
    """Ищет и уничтожает зомби-процессы chrome.exe, которые не привязаны к активному мосту Node."""
    print("[Cleaner] Оптимизация оперативной памяти (поиск зомби-процессов Chrome)...")
    killed_count = 0
    
    # Находим PID активного whatsapp_bridge
    active_bridge_pids = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any('whatsapp_bridge.js' in arg for arg in cmdline):
                active_bridge_pids.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    # Если мост запущен, его дочерние хромы трогать не надо.
    # Но если хром висит как сирота без родителя или если родитель мертв, убиваем его!
    for proc in psutil.process_iter(['pid', 'name', 'ppid']):
        try:
            if proc.info['name'] == 'chrome.exe':
                ppid = proc.info['ppid']
                # Проверяем, жив ли родитель
                parent_exists = psutil.pid_exists(ppid)
                if not parent_exists or (ppid not in active_bridge_pids and ppid != os.getpid()):
                    # Это зомби хром! Убиваем
                    proc.kill()
                    killed_count += 1
                    print(f"[Cleaner] Уничтожен зомби-процесс Chrome с PID {proc.info['pid']} (ppid: {ppid})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    print(f"[Cleaner] Оптимизация ОЗУ завершена. Убито зомби-процессов: {killed_count}")
    return killed_count

def run_garbage_collector():
    """Запускает полную очистку системы."""
    print(f"\n=== [Cleaner Startup: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ===")
    
    # 1. Чистим файлы Syncthing
    deleted_files, bytes_saved = clean_sync_conflicts()
    
    # 2. Ротируем логи
    truncate_logs()
    
    # 3. Чистим зомби процессы Chrome (RAM)
    killed_chromes = kill_zombie_chromes()
    
    print("=== [Cleaner Finished Successfully] ===\n")
    return {
        "deleted_files": deleted_files,
        "bytes_saved_kb": bytes_saved / 1024,
        "killed_chromes": killed_chromes
    }

if __name__ == "__main__":
    run_garbage_collector()
