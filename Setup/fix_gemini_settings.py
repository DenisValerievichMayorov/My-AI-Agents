import json, os

settings = {
    "theme": "Default",
    "selectedAuthType": "oauth-personal"
}

path = os.path.expanduser("~/.gemini/settings.json")
os.makedirs(os.path.dirname(path), exist_ok=True)

with open(path, "w") as f:
    json.dump(settings, f, indent=2)

print(f"✅ settings.json исправлен: {path}")
print(open(path).read())
