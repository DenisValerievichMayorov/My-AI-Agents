import subprocess
import os

def main():
    sync_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    js_path = os.path.join(sync_dir, "whatsapp_bridge.js")
    
    print(f"Starting {js_path} in background...")
    print("Node will handle unbuffered logging directly to whatsapp_bridge.log.")
    
    # Run node process without locking whatsapp_bridge.log on Windows
    process = subprocess.Popen(
        ["node", js_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=sync_dir
    )
    print(f"Node process started with PID: {process.pid}")

if __name__ == "__main__":
    main()
