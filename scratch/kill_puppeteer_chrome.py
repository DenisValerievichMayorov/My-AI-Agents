import psutil
import os

def main():
    print("Scanning for locked Puppeteer Chrome processes...")
    killed_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
        try:
            name = proc.info['name']
            if name and 'chrome' in name.lower():
                exe = proc.info['exe']
                cmdline = proc.info['cmdline']
                
                # Check if it is running from the Puppeteer cache folder or uses the wwebjs auth session
                is_puppeteer = False
                if exe and 'puppeteer' in exe.lower():
                    is_puppeteer = True
                if cmdline and any('.wwebjs_auth' in arg for arg in cmdline):
                    is_puppeteer = True
                    
                if is_puppeteer:
                    print(f"Killing Puppeteer Chrome process PID {proc.pid}: {exe}")
                    proc.kill()
                    killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    print(f"Cleanup complete. Killed {killed_count} locked Puppeteer processes.")

if __name__ == "__main__":
    main()
