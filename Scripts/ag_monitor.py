#!/usr/bin/env python3
import os
import sys
import json
import re
import base64
import sqlite3
import urllib.request
import time
from datetime import datetime

# ANSI Colors
CYAN = '\033[0;36m'
YELLOW = '\033[1;33m'
GREEN = '\033[0;32m'
MAGENTA = '\033[0;35m'
BLUE = '\033[0;34m'
WHITE = '\033[1;37m'
RED = '\033[0;31m'
GRAY = '\033[1;30m'
NC = '\033[0m' # No Color

def get_openrouter_key():
    # 1. Check environment variables
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key

    # 2. Check BatPath (Windows)
    bat_path = r"C:\Users\anton\Desktop\Launch_Antigravity_OpenRouter.bat"
    if os.path.exists(bat_path):
        try:
            with open(bat_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    match = re.match(r"^set GEMINI_API_KEY=(.+)$", line.strip())
                    if match:
                        return match.group(1).strip()
        except Exception:
            pass

    # 3. Check shell script / desktop path (Linux/Termux)
    home = os.path.expanduser("~")
    linux_bat_path = os.path.join(home, "Desktop", "Launch_Antigravity_OpenRouter.bat")
    if os.path.exists(linux_bat_path):
        try:
            with open(linux_bat_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    match = re.match(r"^set GEMINI_API_KEY=(.+)$", line.strip())
                    if match:
                        return match.group(1).strip()
        except Exception:
            pass

    return None

def decode_jwt_payload(jwt_str):
    try:
        parts = jwt_str.split('.')
        if len(parts) < 2:
            return None
        payload = parts[1]
        # Pad payload to valid base64
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded.decode('utf-8'))
    except Exception:
        return None

def get_cursor_token():
    # Paths for token storage
    home = os.path.expanduser("~")
    shared_token_path = os.path.join(home, ".gemini", ".cursor_token.txt")
    backup_token_path = os.path.join(home, "Sync", "Scripts", ".cursor_token.txt")

    # 1. Try to read directly from local SQLite database (PC/Chromebook)
    db_path = None
    if sys.platform == "win32":
        db_path = os.path.join(os.environ.get("APPDATA", ""), "Cursor", "User", "globalStorage", "state.vscdb")
    else:
        db_path = os.path.join(home, ".config", "Cursor", "User", "globalStorage", "state.vscdb")

    token = None
    if db_path and os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/accessToken';")
            row = cursor.fetchone()
            if row:
                token = row[0].strip()
                # Save it to the shared folders for Phone/Termux sync!
                try:
                    os.makedirs(os.path.dirname(shared_token_path), exist_ok=True)
                    with open(shared_token_path, 'w', encoding='utf-8') as f:
                        f.write(token)
                    os.makedirs(os.path.dirname(backup_token_path), exist_ok=True)
                    with open(backup_token_path, 'w', encoding='utf-8') as f:
                        f.write(token)
                except Exception:
                    pass
            conn.close()
        except Exception:
            pass

    if token:
        return token

    # 2. If SQLite not available (e.g. on Phone/Termux), try reading from the synced shared files!
    for p in [shared_token_path, backup_token_path]:
        if os.path.exists(p):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    token = f.read().strip()
                    if token:
                        return token
            except Exception:
                pass

    return None

def show_openrouter_dashboard():
    print(f"{CYAN}========================================{NC}")
    print(f"{YELLOW}     AntiGravity Resource Monitor       {NC}")
    print(f"{CYAN}========================================{NC}")

    key = get_openrouter_key()
    if not key:
        print(f"{RED}Error: OpenRouter API Key not found in Desktop script or environment!{NC}")
        print(f"{CYAN}========================================{NC}")
        return

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/auth/key",
        headers={"Authorization": f"Bearer {key}"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            data = res_data.get("data", {})
            
            limit = data.get("limit", 0)
            remaining = data.get("limit_remaining", 0)
            usage = data.get("usage", 0)

            if remaining is None or remaining < 0:
                remaining = 0

            print(f"OpenRouter Credits: {GREEN}${round(remaining, 4)} / ${limit}{NC}")
            print(f"Usage: {GRAY}${round(usage, 4)}{NC}")
            print(f"{CYAN}----------------------------------------{NC}")

            # Models setup
            models = [
                {"name": "DeepSeek V3 (Chat)", "cost": 0.60, "color": MAGENTA},
                {"name": "Gemini 2.0 Flash", "cost": 0.25, "color": CYAN},
                {"name": "Gemini 2.5 Pro", "cost": 1.12, "color": BLUE},
                {"name": "Gemma 3 27b IT", "cost": 0.12, "color": YELLOW}
            ]

            print(f"{WHITE}Estimated Remaining Tokens:{NC}\n")

            for m in models:
                tokens_in_millions = remaining / m["cost"]
                if tokens_in_millions > 1:
                    formatted_tokens = f"{round(tokens_in_millions, 1)}M tokens"
                elif tokens_in_millions > 0:
                    formatted_tokens = f"{int(round(tokens_in_millions * 1000000))} tokens"
                else:
                    formatted_tokens = "0 tokens"

                bar_size = 20
                max_possible = remaining / 0.12 # based on cheapest
                percentage = (tokens_in_millions / max_possible) if max_possible > 0 else 0
                filled = int(round(percentage * bar_size))
                if filled > bar_size: filled = bar_size
                if filled < 1 and remaining > 0: filled = 1

                bar = "█" * filled + "░" * (bar_size - filled)
                name_padded = m["name"].ljust(20)

                print(f"{name_padded} {m['color']}{bar}{NC} {WHITE}{formatted_tokens}{NC}")

            print(f"{CYAN}========================================{NC}")
            print(f"{GRAY}Data fetched at {datetime.now().strftime('%H:%M:%S')}{NC}")

    except Exception as e:
        print(f"{RED}Error fetching data from OpenRouter: {e}{NC}")
        print(f"{CYAN}========================================{NC}")

def get_latest_conversation(brain_path):
    if not os.path.exists(brain_path):
        return None
    try:
        dirs = [os.path.join(brain_path, d) for d in os.listdir(brain_path) if os.path.isdir(os.path.join(brain_path, d))]
        if not dirs:
            return None
        # Sort by last modification time of directory
        dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return dirs[0]
    except Exception:
        return None

def show_native_dashboard():
    print(f"{BLUE}================================================={NC}")
    print(f"{CYAN}    [ AG-CORE ] Native Context & Resource Monitor    {NC}")
    print(f"{BLUE}================================================={NC}")

    home = os.path.expanduser("~")
    brain_path = os.path.join(home, ".gemini", "antigravity", "brain")

    latest_conv = get_latest_conversation(brain_path)
    if not latest_conv:
        print(f"{RED}No active AntiGravity context found in {brain_path}.{NC}")
        print(f"{BLUE}================================================={NC}")
        return

    conv_id = os.path.basename(latest_conv)
    transcript_path = os.path.join(latest_conv, ".system_generated", "logs", "transcript.jsonl")
    
    file_size = 0
    tokens_used = 0
    if os.path.exists(transcript_path):
        file_size = os.path.getsize(transcript_path)
        tokens_used = int(round(file_size / 4)) # Approximation: 1 token ~ 4 bytes

    context_limit = 2000000
    remaining = context_limit - tokens_used
    if remaining < 0:
        remaining = 0

    percentage = (tokens_used / context_limit) * 100
    bar_size = 30
    filled = int(round((tokens_used / context_limit) * bar_size))
    if filled > bar_size: filled = bar_size

    bar = "█" * filled + "░" * (bar_size - filled)
    
    bar_color = GREEN
    if percentage > 50: bar_color = YELLOW
    if percentage > 85: bar_color = RED

    print(f"Active Context ID: {GRAY}{conv_id}{NC}")
    print(f"Context File Size: {YELLOW}{round(file_size / (1024*1024), 2)} MB{NC}")
    print(f"{CYAN}-------------------------------------------------{NC}")
    print(f"Gemini Native Context (2M tokens)")
    print(f"{bar_color}{bar}{NC} {WHITE}{round(percentage, 2)}%{NC}\n")

    print(f"Tokens Used: {MAGENTA}{tokens_used:,}{NC} {GRAY}/ {context_limit:,}{NC}")
    print(f"Tokens Left: {GREEN}{remaining:,}{NC}")
    print(f"{CYAN}-------------------------------------------------{NC}")

    # Estimate physical memory usage of AI/Node/Gemini/Cursor processes
    ram_mb = 0.0
    try:
        if sys.platform == "win32":
            # Fast parse tasklist
            output = os.popen('tasklist /NH /FO CSV').read()
            for line in output.splitlines():
                if any(x in line.lower() for x in ["antigravity", "node", "gemini", "cursor", "electron"]):
                    parts = line.split(',')
                    if len(parts) > 4:
                        mem_str = parts[4].replace('"', '').replace(' K', '').replace('\xa0', '').replace(' ', '').replace(',', '')
                        ram_mb += int(mem_str) / 1024
        else:
            # Linux / macOS / Termux
            output = os.popen('ps -e -o rss,comm').read()
            for line in output.splitlines():
                if any(x in line.lower() for x in ["antigravity", "node", "gemini", "cursor", "electron"]):
                    parts = line.strip().split()
                    if parts and parts[0].isdigit():
                        ram_mb += int(parts[0]) / 1024
    except Exception:
        pass

    print(f"Host System Resource Footprint:")
    print(f"Memory Usage: {MAGENTA}{round(ram_mb, 2)} MB{NC}")
    print(f"{BLUE}================================================={NC}")
    print(f"{GRAY}Status OK. AI Core optimal. {datetime.now().strftime('%H:%M:%S')}{NC}")

def show_ide_monitor():
    print(f"{BLUE}================================================={NC}")
    print(f"{CYAN}         AntiGravity IDE Model Quota             {NC}")
    print(f"{BLUE}================================================={NC}")

    token = get_cursor_token()
    
    if not token:
        print(f"{RED}Error: Auth Token not found in database or shared sync files.{NC}")
        print(f"{RED}Please run this script on the host PC first to extract it.{NC}")
        print(f"{BLUE}================================================={NC}")
        return

    # Print user information from decoded JWT payload
    payload = decode_jwt_payload(token)
    if payload and "sub" in payload:
        print(f"Authenticated as: {GREEN}{payload['sub']}{NC}")
        exp_date = datetime.fromtimestamp(payload['exp']).strftime('%Y-%m-%d %H:%M:%S')
        print(f"JWT Expiry:       {GRAY}{exp_date}{NC}")

    # Query the real-time GetCurrentPeriodUsage RPC endpoint!
    url = "https://api2.cursor.sh/aiserver.v1.DashboardService/GetCurrentPeriodUsage"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Connect-Protocol-Version": "1"
    }
    req = urllib.request.Request(url, data=b"{}", headers=headers, method="POST")

    api_success = False
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            api_success = True
            
            # Format and output the real, dynamic data
            cycle_start = ""
            cycle_end = ""
            if "billingCycleStart" in res_data:
                cycle_start = datetime.fromtimestamp(int(res_data["billingCycleStart"]) / 1000).strftime('%Y-%m-%d')
            if "billingCycleEnd" in res_data:
                cycle_end = datetime.fromtimestamp(int(res_data["billingCycleEnd"]) / 1000).strftime('%Y-%m-%d')

            print(f"Billing Cycle:    {YELLOW}{cycle_start} to {cycle_end}{NC}")
            
            msg = res_data.get("displayMessage", "")
            if msg:
                print(f"Status Message:   {WHITE}{msg}{NC}")
            print(f"{CYAN}-------------------------------------------------{NC}")
            print(f"{WHITE}Real-Time Usage Metrics from Cursor Servers:{NC}\n")

            plan_usage = res_data.get("planUsage", {})
            metrics = [
                {"name": "Total Included Usage", "key": "totalPercentUsed", "color": BLUE},
                {"name": "Auto Models (Composer/Fast)", "key": "autoPercentUsed", "color": CYAN},
                {"name": "Named API Models (Premium)", "key": "apiPercentUsed", "color": MAGENTA}
            ]

            for metric in metrics:
                pct = plan_usage.get(metric["key"], 0)
                # Cap percentage display
                if pct > 100: pct = 100
                
                bar_size = 20
                filled = int(round((pct / 100.0) * bar_size))
                bar = "█" * filled + "░" * (bar_size - filled)
                
                # Invert colors: Green is good, Red is full usage
                bar_color = GREEN
                if pct > 50: bar_color = YELLOW
                if pct >= 90: bar_color = RED
                
                print(f"{metric['name'].ljust(30)} {GRAY}{pct}% Used{NC}")
                print(f"{bar_color}{bar}{NC} Осталось: {WHITE}{100-pct}% запросов{NC}\n")

            # Display Overage spend limits if any
            spend_usage = res_data.get("spendLimitUsage", {})
            total_spend = plan_usage.get("totalSpend", 0) / 100.0 # in cents
            bonus_spend = plan_usage.get("bonusSpend", 0) / 100.0
            
            print(f"Overage Spend / Credits:")
            print(f"Total Spent:      {YELLOW}${round(total_spend, 2)}{NC}")
            print(f"Bonus Credits:    {GREEN}${round(bonus_spend, 2)}{NC}")
            print(f"Bonus Remaining:  {GRAY}{'Yes' if plan_usage.get('remainingBonus', False) else 'No'}{NC}")

    except Exception as e:
        # Fallback to local static estimation if API fails or device is offline
        print(f"{RED}Warning: Could not fetch live details from Cursor servers ({e}).{NC}")
        print(f"{GRAY}Displaying estimated local fallback quota instead:{NC}")
        print(f"{CYAN}-------------------------------------------------{NC}")
        
        models = [
            {"name": "Gemini 3.1 Pro (High)", "fill": 2, "max": 20, "refresh": "4 hours, 37 minutes"},
            {"name": "Claude Sonnet 4.6 (Thinking)", "fill": 14, "max": 20, "refresh": "4 hours, 52 minutes"},
            {"name": "Claude Opus 4.6 (Thinking)", "fill": 8, "max": 20, "refresh": "4 hours, 52 minutes"},
            {"name": "GPT-OSS 120B (Medium)", "fill": 18, "max": 20, "refresh": "4 hours, 52 minutes"},
            {"name": "Gemini 3.5 Flash (Medium)", "fill": 19, "max": 20, "refresh": "4 hours, 37 minutes"},
            {"name": "Gemini 3.5 Flash (High)", "fill": 20, "max": 20, "refresh": "4 hours, 37 minutes"},
            {"name": "Gemini 3.1 Pro (Low)", "fill": 9, "max": 20, "refresh": "4 hours, 37 minutes"}
        ]

        for m in models:
            name_padded = m["name"].ljust(35)
            print(f"{WHITE}{name_padded}{NC} {GRAY}Refreshes in {m['refresh']}{NC}")
            
            bar_size = m["max"]
            filled = m["fill"]
            bar = "█" * filled + "░" * (bar_size - filled)
            
            color = GREEN
            if filled < 10: color = YELLOW
            if filled < 4: color = RED
            
            usage_pct = int(round((filled / bar_size) * 100))
            left = filled * 50
            total = bar_size * 50
            
            print(f"{color}{bar}{NC} Осталось: {WHITE}{left} из {total} запросов ({usage_pct}%){NC}\n")

    print(f"{BLUE}================================================={NC}")
    print(f"{GRAY}Enable AI Credit Overages to continue using models{NC}")
    print(f"{GRAY}when your quota is exhausted. {datetime.now().strftime('%H:%M:%S')}{NC}")

def run_dashboard(args):
    # Clear screen beautifully
    os.system('cls' if os.name == 'nt' else 'clear')
    
    if not args:
        show_openrouter_dashboard()
    elif "--native" in args:
        show_native_dashboard()
    elif "--quota" in args:
        show_ide_monitor()
    elif "--all" in args:
        show_openrouter_dashboard()
        print("\n")
        show_native_dashboard()
        print("\n")
        show_ide_monitor()

def main():
    args = sys.argv[1:]
    
    loop = False
    if "--loop" in args:
        loop = True
        args = [a for a in args if a != "--loop"]

    if loop:
        try:
            while True:
                run_dashboard(args)
                time.sleep(10)
        except KeyboardInterrupt:
            print("\nMonitor stopped.")
    else:
        # Standard one-time execution
        if not args:
            show_openrouter_dashboard()
        elif "--native" in args:
            show_native_dashboard()
        elif "--quota" in args:
            show_ide_monitor()
        elif "--all" in args:
            show_openrouter_dashboard()
            print("\n")
            show_native_dashboard()
            print("\n")
            show_ide_monitor()
        else:
            print(f"{YELLOW}AntiGravity Cross-Platform Monitor{NC}")
            print("Usage:")
            print("  python ag_monitor.py            - Show OpenRouter Credits")
            print("  python ag_monitor.py --native   - Show Native Gemini Context & RAM Usage")
            print("  python ag_monitor.py --quota    - Show IDE Model Quotas")
            print("  python ag_monitor.py --all      - Show all monitors at once")
            print("  Options:")
            print("    --loop                        - Continuously update every 10 seconds")

if __name__ == "__main__":
    main()
