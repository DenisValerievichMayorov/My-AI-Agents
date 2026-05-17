import os
import subprocess
import time
import urllib.request
import json

def main():
    print("Stopping active Ollama processes...")
    if os.name == 'nt':
        subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], capture_output=True)
    else:
        subprocess.run(["pkill", "-f", "ollama"], capture_output=True)
        
    time.sleep(2)
    
    ollama_path = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe")
    if not os.path.exists(ollama_path):
        ollama_path = "ollama"
        
    print(f"Starting Ollama with OLLAMA_HOST=0.0.0.0 binding using {ollama_path}...")
    env = os.environ.copy()
    env["OLLAMA_HOST"] = "0.0.0.0"
    
    # Run in background
    subprocess.Popen([ollama_path, "serve"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait for startup
    time.sleep(4)
    
    # Verify binding by hitting 127.0.0.1:11434/api/tags
    try:
        req = urllib.request.urlopen("http://127.0.0.1:11434/api/tags")
        data = json.loads(req.read().decode())
        print("Ollama successfully restarted and listening on 0.0.0.0:11434!")
        print("Available models:")
        for m in data.get('models', []):
            print(f"  - {m['name']}")
    except Exception as e:
        print(f"Failed to verify Ollama status: {e}")

if __name__ == "__main__":
    main()
