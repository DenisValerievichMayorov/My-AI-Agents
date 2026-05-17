import os
import subprocess
import urllib.request
import json

def find_ollama():
    paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
        r"C:\Program Files\Ollama\ollama.exe",
        r"C:\Program Files (x86)\Ollama\ollama.exe"
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None

def test_ollama_api():
    try:
        req = urllib.request.urlopen("http://localhost:11434/api/tags")
        data = json.loads(req.read().decode())
        print("Ollama API is running locally! Available models:")
        for model in data.get('models', []):
            print(f" - {model['name']}")
        return True
    except Exception as e:
        print(f"Could not connect to local Ollama API (localhost:11434): {e}")
        return False

def main():
    p = find_ollama()
    if p:
        print(f"Found Ollama binary at: {p}")
        try:
            res = subprocess.run([p, "list"], capture_output=True, text=True)
            print("Output of 'ollama list':")
            print(res.stdout)
        except Exception as e:
            print(f"Error running ollama list: {e}")
    else:
        print("Ollama binary not found on Windows PC.")
        
    test_ollama_api()

if __name__ == "__main__":
    main()
