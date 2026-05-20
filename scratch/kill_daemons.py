import psutil
import os

def kill_daemons():
    current_pid = os.getpid()
    killed_count = 0
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            name = p.info['name']
            if name and name.lower() == 'python.exe' and p.info['pid'] != current_pid:
                cmdline = p.info['cmdline'] or []
                cmd_str = ' '.join(cmdline).lower()
                if 'agent_listener' in cmd_str or 'heartbeat' in cmd_str:
                    print(f"Attempting to kill PID {p.info['pid']}: {cmdline}")
                    p.kill()
                    print(f"Successfully killed PID {p.info['pid']}")
                    killed_count += 1
        except Exception as e:
            print(f"Failed to kill process: {e}")
            
    print(f"Killed {killed_count} background processes.")

if __name__ == '__main__':
    kill_daemons()
