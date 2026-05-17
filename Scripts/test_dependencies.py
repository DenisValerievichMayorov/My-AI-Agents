#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import socket
import subprocess

DEVICE_NAME = socket.gethostname()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print(f"=== DIAGNOSTICS REPORT FOR GMC NODE: [{DEVICE_NAME}] ===")

def check_package(name):
    try:
        __import__(name)
        return "✅ OK (Installed)"
    except ImportError as e:
        return f"❌ FAILED (Missing: {str(e)})"

def get_cli_command():
    if os.name == 'nt':
        npm_path = os.path.join(os.environ.get('APPDATA', ''), 'npm', 'gemini.cmd')
        if os.path.isfile(npm_path): return npm_path
        return "gemini.cmd"
    candidates = [
        os.path.expanduser("/home/denisvalerievichmayorov1/.npm-global/bin/gemini"),
        os.path.expanduser("~/.local/bin/gemini"),
        "/usr/local/bin/gemini",
        "/usr/bin/gemini",
        "gemini"
    ]
    for path in candidates:
        if os.path.isfile(path): return path
    return "gemini"

# 1. Проверка пакетов Python
print("\n--- 1. Python Package Checks ---")
packages = ["googleapiclient", "google_auth_oauthlib", "geopy", "fpdf", "urllib.request"]
for pkg in packages:
    print(f"- {pkg}: {check_package(pkg)}")

# 2. Проверка файлов авторизации Google
print("\n--- 2. Google OAuth Credentials & Tokens ---")
files = {
    "credentials.json": os.path.join(BASE_DIR, "credentials.json"),
    "google_token.json": os.path.join(BASE_DIR, "google_token.json")
}
for name, path in files.items():
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"- {name}: ✅ Present ({size} bytes)")
    else:
        print(f"- {name}: ❌ MISSING (Path: {path})")

# 3. Проверка Gemini CLI
print("\n--- 3. Gemini CLI Executive Check ---")
cli_path = get_cli_command()
print(f"- Detected CLI Path: {cli_path}")

try:
    res = subprocess.run([cli_path, "--help"], capture_output=True, text=True, timeout=5)
    print(f"- Executable test: ✅ OK (Exit Code: {res.returncode})")
except Exception as e:
    print(f"- Executable test: ❌ FAILED ({str(e)})")

print("\n==========================================")
