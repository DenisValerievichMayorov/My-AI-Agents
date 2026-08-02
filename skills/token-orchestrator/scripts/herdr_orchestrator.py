#!/usr/bin/env python3
"""
Herdr Granite Orchestrator (Daemon Mode with Master Agent Communication and Auto-Restart)

Политика (2026-07-15+, post FREE-AGENTS-163832 lessons):
1) Heartbeat/status screen ALWAYS before expensive LLM — master never sees stale "no workers".
2) Rule-based analysis is PRIMARY; LLM only for ambiguous cases (USE_LLM_ANALYSIS).
3) Interactive tencent/hy3: CHAT only. Tool/write tasks → orfree via send_orfree_task.ps1 (pi -p).
4) Detect fake tools (XML tool_call, "write ..." without filesystem commit) → CANCEL + REPORT + reassign hint.
5) Detect stuck Working... (unchanged log N cycles) → interrupt + report.
6) Outbox seq persists across restarts; cold-start does not chat-spam "no workers".
7) Artifact path promises in log are verified on disk.
"""

import sys
import os
import re
import json
import time
import subprocess
import urllib.request
import urllib.error

# Настройки путей и API
# LLM для анализа логов: cloud free only (local Ollama removed 2026-08-02).
ORCH_MODEL_PRIMARY = "openrouter/tencent/hy3:free"
MODEL_NAME = ORCH_MODEL_PRIMARY
HERDR_BIN = r"C:\Users\anton\AppData\Local\Programs\Herdr\bin\herdr.exe"
PI_CLI = r"C:\Users\anton\AppData\Roaming\npm\node_modules\@earendil-works\pi-coding-agent\dist\cli.js"
CHECK_INTERVAL_SEC = 15  # Сканируем чаще для быстрого отклика
MASTER_PANE_ID = "w2:p31"  # ID мастер-панели (agy-main)
# НЕ вставлять текст+Enter в окно Grok (ломает набор / mid-turn).
# True = agent send + Return. False = outbox + latest screen + notify (master читает файл).
MASTER_INJECT_CHAT = False
# Если True и master idle — push status line в chat Grok (шумит при idle-herd).
# 2026-07-15: False — status только в orch_status_latest.md + badge; chat не спамим.
MASTER_PUSH_SCREEN_WHEN_IDLE = False
# Не пушить в chat "no workers" в первые N сек после старта (race: workers ещё регистрируются).
COLD_START_SEC = 45
# LLM analysis OFF by default — free models slow/block heartbeat; rule-based is reliable.
USE_LLM_ANALYSIS = False
ORCH_OUTBOX = r"C:\Users\anton\Sync\Data\orch_to_master.jsonl"
ORCH_STATUS_LATEST = r"C:\Users\anton\Sync\Data\orch_status_latest.json"
ORCH_STATUS_MD = r"C:\Users\anton\Sync\Data\orch_status_latest.md"
QUERY_TIMEOUT_SEC = 45  # shorter — never block daemon for 90s×N workers
LOG_TRUNCATE_CHARS = 1200
_outbox_seq = 0
_orch_started_at = 0.0

# Tool-task routing
SEND_ORFREE_PS1 = r"C:\Users\anton\Sync\skills\herdr-orchestrator\scripts\send_orfree_task.ps1"
ARTIFACT_ROOTS = (
    r"C:\Users\anton\Sync\Data\collab_tests",
    r"C:\Users\anton\Sync\Data",
)
# Stuck thresholds (cycles × CHECK_INTERVAL_SEC)
STUCK_WORKING_CYCLES = 4       # ~60s same Working... log
FAKE_TOOL_CYCLES = 2           # ~30s after fake-tool signals
PROMISED_PATH_GRACE_CYCLES = 3 # ~45s after path promised before fail

# Конфигурация запуска. ОБЯЗАТЕЛЬНО -ne: конфликт packages web_search ломает pi без -ne.
# tools: полный набор (AGENTS.md §9 — не --no-tools).
_PI = r"C:\Users\anton\AppData\Roaming\npm\pi.cmd"
_TOOLS = "read,bash,edit,write,grep,find,ls"
# 2026-08-02: cerebras/mistral/groq removed. Only or-free / nvidia / ollama-cloud.
AGENT_LAUNCH_COMMANDS = {
    "pi-ling": rf"{_PI} -ne --provider or-free --model inclusionai/ling-3.0-flash:free --tools {_TOOLS}",
    "pi-orfree": rf"{_PI} -ne --provider or-free --model nvidia/nemotron-3-super-120b-a12b:free --tools {_TOOLS}",
    "hy3-orfree": rf"{_PI} -ne --provider or-free --model nvidia/nemotron-3-super-120b-a12b:free --tools {_TOOLS}",
    "pi-nemotron": rf"{_PI} -ne --provider or-free --model nvidia/nemotron-3-super-120b-a12b:free --tools {_TOOLS}",
    "pi-ollama-cloud": rf"{_PI} -ne --provider ollama-cloud --model minimax-m3 --tools {_TOOLS}",
    "pi-nvidia": rf"{_PI} -ne --provider nvidia --model openai/gpt-oss-20b --tools {_TOOLS}",
}
PREFERRED_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
PREFERRED_CHAT_MODEL = "inclusionai/ling-3.0-flash:free"
FALLBACK_MODELS = [
    "or-free/inclusionai/ling-3.0-flash:free",
    "or-free/nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/openai/gpt-oss-20b",
    "ollama-cloud/minimax-m3",
    "or-free/openrouter/free",
]
# Toolish DELEGATE order (no cerebras/mistral/groq)
TOOL_WORKER_ORDER = (
    "pi-ling", "ling",
    "pi-orfree", "orfree", "hy3-orfree",
    "pi-nemotron", "nemotron",
    "pi-ollama-cloud", "ollama-cloud",
    "pi-nvidia", "nvidia",
)

# Для отслеживания отсутствия активности
last_agent_outputs = {}  # label -> last log
no_activity_count = {}   # label -> consecutive no-change cycles
stuck_working_count = {}  # label -> consecutive same-log while Working...
promised_path_count = {}  # label|path -> cycles missing on disk
reported_no_activity = {} # label -> boolean whether we already reported no activity
reported_result_hash = {}  # label -> stable fingerprint of last RESULT (anti-spam)
fake_tool_reported = {}  # label -> last report unix (anti-spam)
# Persist fingerprints across restarts to avoid re-spam
_REPORT_STATE_PATH = r"C:\Users\anton\Sync\Data\herdr_orch_reported.json"


def _load_report_state():
    global reported_result_hash
    try:
        if os.path.isfile(_REPORT_STATE_PATH):
            with open(_REPORT_STATE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                reported_result_hash.update(data)
    except Exception as e:
        print(f"[Orchestrator] report state load fail: {e}")


def _save_report_state():
    try:
        os.makedirs(os.path.dirname(_REPORT_STATE_PATH), exist_ok=True)
        with open(_REPORT_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(reported_result_hash, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Orchestrator] report state save fail: {e}")


def stable_result_fingerprint(label, terminal_log):
    """Fingerprint by RESULT lines / paths — not by LLM rephrasing."""
    log = terminal_log or ""
    keys = []
    for m in re.finditer(r"RESULT:\s*(\S[^\n]{0,120})", log, flags=re.I):
        keys.append(m.group(0).strip()[:140])
    for m in re.finditer(r"(token_[ab]_\d{8}-\d{6}\.txt|NEMO-FILE-OK|ORFREE-CHAIN-OK|PONG-NEMO|FREE-AGENTS-)", log, flags=re.I):
        keys.append(m.group(0))
    if not keys:
        # fallback: short hash of last 400 chars of log (only when no RESULT)
        keys.append(str(hash(log[-400:])) if log else "empty")
    # unique preserve order
    seen = set()
    uniq = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            uniq.append(k)
    return f"{label}|" + "|".join(uniq[-5:])


def is_orfree_lane(label, name=""):
    s = f"{label or ''} {name or ''}".lower()
    return "orfree" in s


def is_interactive_lane(label, name=""):
    s = f"{label or ''} {name or ''}".lower()
    # chat-only hy3 interactive (not nemotron free worker)
    return "interactive" in s or "tencet" in s or s.strip() in ("hy3-interactive",)


def is_tool_worker_lane(label, name=""):
    """or-free / nvidia / ollama-cloud workers — allowed for tool/write tasks."""
    s = f"{label or ''} {name or ''}".lower()
    if is_interactive_lane(label, name):
        return False
    return any(
        x in s
        for x in (
            "orfree", "ling", "nemotron", "ollama-cloud", "nvidia",
            "pi-ling", "pi-orfree", "pi-nemotron", "pi-ollama-cloud", "pi-nvidia",
        )
    )


def pick_tool_worker_pane(agents):
    """First idle/ready tool worker by TOOL_WORKER_ORDER (ling → orfree → nemotron…)."""
    if not agents:
        return None
    scored = []
    for a in agents:
        lab = (a.get("label") or "")
        name = (a.get("name") or "")
        s = f"{lab} {name}".lower()
        if is_orch_or_master_pane(a) or is_interactive_lane(lab, name):
            continue
        if not is_tool_worker_lane(lab, name):
            continue
        st = (a.get("agent_status") or "").lower()
        if st in ("working", "blocked"):
            continue
        rank = 999
        for i, key in enumerate(TOOL_WORKER_ORDER):
            if key in s:
                rank = i
                break
        scored.append((rank, a.get("pane_id"), lab or name))
    if not scored:
        return None
    scored.sort(key=lambda t: t[0])
    return scored[0][1]


def is_orch_or_master_pane(agent):
    """True if pane is master or orchestrator (never analyze / never count as worker)."""
    lab = (agent.get("label") or "").lower()
    name = (agent.get("name") or "").lower()
    pid = agent.get("pane_id") or ""
    combined = f"{lab} {name}"
    if pid == MASTER_PANE_ID:
        return True
    if any(x in combined for x in (
        "granite-orchestrator", "granite orchestrator", "orch-hy3",
        "agy-main", "agy_main", "grok master", "grok-master",
    )):
        return True
    # Label "ORCH hy3" but not "tencent-hy3 orfree/interactive"
    if "orch" in lab and "orfree" not in combined and "interactive" not in combined and "tencent-hy3" not in lab:
        return True
    if name in ("grok", "agy-main", "granite-orchestrator"):
        return True
    return False


def extract_promised_paths(log):
    """Paths the agent claims to write (Windows + forward slashes)."""
    log = log or ""
    paths = []
    # C:/... or C:\... ending with common artifact extensions
    for m in re.finditer(
        r"(?:[A-Za-z]:[\\/][^\s\"'`\n]+?\.(?:md|txt|json|jsonl|csv|js|ps1|py))",
        log,
        flags=re.I,
    ):
        p = m.group(0).strip().rstrip(").,;:]")
        # normalize
        p = p.replace("/", "\\")
        if len(p) > 12:
            paths.append(p)
    # unique preserve order
    seen = set()
    out = []
    for p in paths:
        pl = p.lower()
        if pl not in seen:
            seen.add(pl)
            out.append(p)
    return out[:12]


def detect_fake_tool_signals(log):
    """
    Interactive hy3 often invents tool use as plain text:
    - XML <tool_call> / <function=...>
    - 'write ...' with expanded content but no real Took from write tool
    Returns list of signal strings.
    """
    log = log or ""
    signals = []
    if re.search(r"<tool_call>|<function\s*=|</tool_call>", log, flags=re.I):
        signals.append("xml_tool_call")
    # pi shows real tools as `$ cmd` or `write path` with Took — fake often has "write ..." alone + Working
    if re.search(r"\bwrite\s+\.\.\.", log, flags=re.I):
        signals.append("write_ellipsis")
    if re.search(r"\bwrite\b[^\n]{0,80}\.(?:md|txt|json)", log, flags=re.I) and "Took " not in log[-800:]:
        # write mentioned with path but no recent Took
        if "Working..." in log or "Writing" in log or "write ..." in log.lower():
            signals.append("write_without_took")
    if "tool_calls" in log.lower() and "fake" in log.lower():
        signals.append("fake_tool_mention")
    return signals


def missing_promised_artifacts(log):
    """Return promised paths that do not exist on disk (under known roots preferred)."""
    missing = []
    for p in extract_promised_paths(log):
        # only care about Sync/Data style artifacts (not random system paths)
        pl = p.lower()
        if "sync\\data" not in pl and "sync/data" not in p.replace("\\", "/").lower():
            continue
        if not os.path.isfile(p):
            missing.append(p)
    return missing


def interrupt_agent(pane_id, label, reason):
    """Escape + Ctrl+C to break fake-tool / stuck Working loops."""
    print(f"[{label}] INTERRUPT: {reason}")
    try:
        run_herdr_cmd(["pane", "send-keys", pane_id, "Escape"])
        time.sleep(0.2)
        run_herdr_cmd(["pane", "send-keys", pane_id, "Ctrl+c"])
        time.sleep(0.4)
        run_herdr_cmd(["pane", "send-keys", pane_id, "Ctrl+c"])
        time.sleep(0.3)
        # short note into pane (no long prompt spam)
        note = f"ORCH: interrupted — {reason[:120]}. Tool tasks → send_orfree_task.ps1 (pi -p)."
        run_herdr_cmd(["pane", "send-text", pane_id, note])
        time.sleep(0.2)
        run_herdr_cmd(["pane", "send-keys", pane_id, "Return"])
    except Exception as e:
        print(f"[{label}] interrupt fail: {e}")


def report_problem_to_master(label, reason, extra=""):
    """Rate-limited problem report (fake tool / stuck / missing artifact)."""
    now = time.time()
    last = fake_tool_reported.get(label, 0)
    if now - last < 120:
        print(f"[{label}] problem report suppressed (anti-spam 120s)")
        return
    fake_tool_reported[label] = now
    body = f"{label}: {reason}"
    if extra:
        body += f" | {extra[:200]}"
    body += " | fix: tool work via send_orfree_task.ps1 / pi -p; interactive=chat only"
    print(f"[{label}] REPORT problem → master: {body[:160]}")
    deliver_report_to_master(label, body[:400])


def is_cold_start():
    return _orch_started_at > 0 and (time.time() - _orch_started_at) < COLD_START_SEC


def get_master_status():
    """idle|working|blocked|unknown for MASTER_PANE_ID."""
    raw = run_herdr_cmd(["pane", "get", MASTER_PANE_ID])
    if not raw:
        return "unknown"
    try:
        data = json.loads(raw)
        pane = data.get("result", {}).get("pane", {}) or {}
        return (pane.get("agent_status") or "unknown").lower()
    except Exception:
        return "unknown"


def wait_master_idle(timeout_sec=25):
    """Wait until master idle so Enter submits report as a new message."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        st = get_master_status()
        if st in ("idle", "unknown", ""):
            return st or "idle"
        print(f"[Master] status={st}, wait idle for report Enter...")
        time.sleep(2)
    return get_master_status()


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def now_unix():
    return int(time.time())


def _ensure_outbox_seq():
    """Continue seq from last line of outbox after restart (no seq=1 reset)."""
    global _outbox_seq
    if _outbox_seq > 0:
        return
    try:
        if not os.path.isfile(ORCH_OUTBOX):
            return
        last = None
        with open(ORCH_OUTBOX, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    last = line
        if last:
            data = json.loads(last)
            _outbox_seq = int(data.get("seq") or 0)
    except Exception:
        pass


def append_outbox(label, report_content, kind="event"):
    """Append timestamped event for master (order + staleness)."""
    global _outbox_seq
    try:
        os.makedirs(os.path.dirname(ORCH_OUTBOX), exist_ok=True)
        _ensure_outbox_seq()
        _outbox_seq += 1
        rec = {
            "seq": _outbox_seq,
            "ts": now_iso(),
            "unix": now_unix(),
            "kind": kind,
            "label": label,
            "text": report_content[:2000],
        }
        with open(ORCH_OUTBOX, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec
    except Exception as e:
        print(f"[Outbox] write fail: {e}")
        return None


def write_status_screen(extra_event=None):
    """
    Снимок состояния с временем — master (Grok) читает это для очерёдности.
    Файлы:
      orch_status_latest.json  — machine
      orch_status_latest.md    — human
    """
    try:
        agents = get_herdr_agents()
        rows = []
        for a in agents:
            lab = a.get("label") or a.get("name") or "?"
            rows.append({
                "label": lab,
                "name": a.get("name"),
                "pane_id": a.get("pane_id"),
                "status": a.get("agent_status") or "unknown",
                "focused": bool(a.get("focused")),
            })
        screen = {
            "screen_ts": now_iso(),
            "screen_unix": now_unix(),
            "preferred_model": PREFERRED_MODEL,
            "snapshot": herd_status_snapshot(),
            "agents": rows,
            "last_event": extra_event,
            "note": "Если now - screen_unix > 180s — снимок устарел. Читай seq/ts для очерёдности.",
        }
        os.makedirs(os.path.dirname(ORCH_STATUS_LATEST), exist_ok=True)
        with open(ORCH_STATUS_LATEST, "w", encoding="utf-8") as f:
            json.dump(screen, f, ensure_ascii=False, indent=2)

        md = [
            f"# Orch status screen",
            f"",
            f"**screen_ts:** `{screen['screen_ts']}`  ",
            f"**screen_unix:** `{screen['screen_unix']}`  ",
            f"**snapshot:** `{screen['snapshot']}`  ",
            f"",
            f"| Pane | Status | id |",
            f"|------|--------|-----|",
        ]
        for r in rows:
            md.append(f"| {r['label']} | {r['status']} | `{r['pane_id']}` |")
        if extra_event:
            md += [
                "",
                "## Last event",
                f"- seq: `{extra_event.get('seq')}`",
                f"- ts: `{extra_event.get('ts')}`",
                f"- label: `{extra_event.get('label')}`",
                f"- text: {extra_event.get('text', '')[:400]}",
            ]
        md += [
            "",
            "_Grok: сверяй `screen_unix` с текущим временем; события в `orch_to_master.jsonl` по `seq`._",
            "",
        ]
        with open(ORCH_STATUS_MD, "w", encoding="utf-8") as f:
            f.write("\n".join(md))
        return screen
    except Exception as e:
        print(f"[StatusScreen] fail: {e}")
        return None


def deliver_report_to_master(label, report_content):
    """
    Timestamped delivery for master orientation (order + freshness).
    Default: outbox + status screen + notify (no chat hijack).
    """
    # Явная метка времени в тексте (для чата / логов)
    ts = now_iso()
    unix = now_unix()
    body = report_content.strip()
    stamped = f"ts={ts} unix={unix} | {body}"
    msg = f"[{label}] {stamped}"
    if len(msg) > 550:
        msg = msg[:550] + "…"

    rec = append_outbox(label, stamped, kind="report")
    screen = write_status_screen(extra_event=rec)
    print(f"[Master] screen_ts={ts} outbox: {msg[:120]}")

    # badge: show ts so UI shows freshness
    badge = f"{ts[-8:]} {body[:90]}"
    try:
        run_herdr_cmd([
            "pane", "report-metadata", MASTER_PANE_ID,
            "--source", MASTER_PANE_ID,
            "--display-agent", (label or "orch")[:40],
            "--custom-status", badge[:120],
        ])
    except Exception:
        pass
    try:
        run_herdr_cmd([
            "notification", "show", f"{label} @ {ts[-8:]}",
            "--body", body[:160],
            "--sound", "done",
        ])
    except Exception:
        pass

    # Optional: push one line to Grok only when idle (timestamp first for ordering)
    if MASTER_PUSH_SCREEN_WHEN_IDLE and not MASTER_INJECT_CHAT:
        st = get_master_status()
        if st == "idle":
            line = f"[orch-screen ts={ts} unix={unix}] {label}: {body[:280]}"
            run_herdr_cmd(["agent", "send", MASTER_PANE_ID, line])
            time.sleep(0.25)
            run_herdr_cmd(["pane", "send-keys", MASTER_PANE_ID, "Return"])
            print(f"[Master] idle-push screen line with ts={ts}")
        else:
            print(f"[Master] skip chat push (status={st}); use {ORCH_STATUS_LATEST}")

    if MASTER_INJECT_CHAT:
        st = wait_master_idle(timeout_sec=10)
        print(f"[Master] inject chat, status={st}")
        ok = run_herdr_cmd(["agent", "send", MASTER_PANE_ID, msg])
        if not ok:
            run_herdr_cmd(["pane", "send-text", MASTER_PANE_ID, msg])
        time.sleep(0.4)
        run_herdr_cmd(["pane", "send-keys", MASTER_PANE_ID, "Return"])
        print(f"[Master] report submitted with Enter → {MASTER_PANE_ID}")
    return True

def run_herdr_cmd(args):
    try:
        my_env = os.environ.copy()
        my_env["HERDR_SOCKET_PATH"] = r"C:\Users\anton\AppData\Roaming\herdr\herdr.sock"
        res = subprocess.run([HERDR_BIN] + args, capture_output=True, text=True, check=True, env=my_env)
        return res.stdout
    except Exception as e:
        stderr_val = getattr(e, 'stderr', '')
        print(f"[Herdr CMD Error] Args {args}: {e}. Stderr: {stderr_val}")
        return ""

def get_herdr_agents():
    raw = run_herdr_cmd(["pane", "list"])
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data.get("result", {}).get("panes", [])
    except Exception:
        return []




def query_llm(prompt, model=None):
    """Вызов pi -p для анализа. -ne обязателен (конфликт web_search extensions)."""
    cli_path = PI_CLI
    if not os.path.exists(cli_path):
        alt = r"C:\Users\anton\AppData\Roaming\npm\node_modules\pi-coding-agent\dist\cli.js"
        if os.path.exists(alt):
            cli_path = alt
        else:
            print("[Orchestrator] pi CLI not found")
            return ""

    # Обрезаем промпт — иначе free-модели / timeout
    if len(prompt) > 3500:
        prompt = prompt[:1500] + "\n...[truncated]...\n" + prompt[-1500:]

    model = model or ORCH_MODEL_PRIMARY
    # model вида openrouter/tencent/hy3:free → provider + model id
    provider = None
    model_id = model
    if model.startswith("openrouter/"):
        provider = "openrouter"
        model_id = model[len("openrouter/"):]
    cmd = [
        "node", cli_path,
        "-ne",
        "-p", prompt,
        "--no-session",
        "--no-context-files",
        "--no-skills",
        "--no-tools",
        "--model", model_id,
    ]
    if provider:
        cmd.extend(["--provider", provider])

    try:
        res = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            timeout=QUERY_TIMEOUT_SEC, check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
        err = (res.stderr or res.stdout or "")[-400:]
        print(f"[Orchestrator] LLM rc={res.returncode} model={model}: {err}")
    except subprocess.TimeoutExpired:
        print(f"[Orchestrator] LLM timeout ({QUERY_TIMEOUT_SEC}s) model={model}")
    except Exception as e:
        print(f"[Orchestrator] LLM error model={model}: {e}")
    return ""


def query_granite(prompt):
    """Primary: openrouter free. Else empty → rule_based_analysis. No local Ollama."""
    out = query_llm(prompt, ORCH_MODEL_PRIMARY)
    if out:
        return out
    print("[Orchestrator] LLM unavailable — use rule_based_analysis")
    return ""


def rule_based_analysis(label, terminal_log, status, *, stuck_working=False, fake_signals=None, missing_paths=None):
    """Детерминированный primary-анализ (LLM optional)."""
    log = terminal_log or ""
    log_l = log.lower()
    at_prompt = "~ (main)" in log
    working = "Working..." in log or status == "working"
    crashed_ps = ("PS C:\\Users" in log and "~ (main)" not in log and "pi.ps1" not in log)
    # Strict API error patterns — avoid false positives from research text about "429-risk" / "quota"
    rate = bool(re.search(
        r"(?i)(HTTP\s*429|status[=:\s]+429|error[^.\n]{0,40}429|"
        r"rate[- ]?limit(?:ed|s)?\s*(?:exceeded|hit|error)|"
        r"too many requests|"
        r"quota\s*(?:exceeded|exhausted)|"
        r"provider\s+returned\s+error)",
        log,
    ))
    err = bool(re.search(
        r"(?i)(^\s*error:|failed to (?:connect|fetch|start)|connection (?:error|refused)|econnrefused)",
        log,
        flags=re.M,
    ))
    high_ctx = bool(re.search(r"CH9\d\.\d%|CH8[5-9]\.\d%", log))
    # Only treat RESULT as "fresh" if near end of pane (avoid re-report from old scrollback)
    tail = log[-900:] if log else ""
    has_result = bool(re.search(r"(?i)RESULT:\s*\S", tail)) and at_prompt
    fake_signals = fake_signals or []
    missing_paths = missing_paths or []

    # Priority 0: fake tools / missing artifacts (interactive hy3 classic)
    if fake_signals and (stuck_working or working or missing_paths):
        sig = ",".join(fake_signals)
        miss = "; ".join(missing_paths[:3]) if missing_paths else "n/a"
        return (
            f"АНАЛИЗ: {label} fake-tool hang signals={sig} missing={miss}\n"
            f"СОСТОЯНИЕ: fake_tool\n"
            f"РЕШЕНИЕ: INTERRUPT_FAKE_TOOL\n"
            f"ОТЧЕТ ДЛЯ МАСТЕРА: {label} fake tools ({sig}); promised missing: {miss}. Reassign tools to orfree/pi -p.\n"
            f"DELEGATE: {label}\n"
            f"TASK: none"
        )
    if missing_paths and at_prompt and not has_result:
        miss = "; ".join(missing_paths[:3])
        return (
            f"АНАЛИЗ: {label} promised artifacts missing on disk: {miss}\n"
            f"СОСТОЯНИЕ: missing_artifact\n"
            f"РЕШЕНИЕ: REPORT TO MASTER\n"
            f"ОТЧЕТ ДЛЯ МАСТЕРА: {label} claimed write but file missing: {miss}. Master/orfree must write.\n"
            f"DELEGATE: {label}\n"
            f"TASK: none"
        )
    if stuck_working:
        return (
            f"АНАЛИЗ: {label} Working... log unchanged ≥{STUCK_WORKING_CYCLES} cycles (~{STUCK_WORKING_CYCLES * CHECK_INTERVAL_SEC}s)\n"
            f"СОСТОЯНИЕ: stuck\n"
            f"РЕШЕНИЕ: INTERRUPT_STUCK\n"
            f"ОТЧЕТ ДЛЯ МАСТЕРА: {label} stuck Working... — interrupted. Prefer shorter task or orfree pi -p.\n"
            f"DELEGATE: {label}\n"
            f"TASK: none"
        )

    if crashed_ps:
        if is_orfree_lane(label):
            return (
                f"АНАЛИЗ: {label} в PowerShell — штатно для orfree (pi -p worker)\n"
                f"СОСТОЯНИЕ: idle\n"
                f"РЕШЕНИЕ: NO ACTION\n"
                f"DELEGATE: {label}\n"
                f"TASK: none"
            )
        return (
            f"АНАЛИЗ: {label} упал в PowerShell (нет сессии pi)\n"
            f"СОСТОЯНИЕ: crashed\n"
            f"РЕШЕНИЕ: RESTART\n"
            f"DELEGATE: {label}\n"
            f"TASK: none"
        )
    if rate:
        return (
            f"АНАЛИЗ: {label} rate-limit/quota\n"
            f"СОСТОЯНИЕ: rate_limited\n"
            f"РЕШЕНИЕ: REPORT TO MASTER\n"
            f"ОТЧЕТ ДЛЯ МАСТЕРА: {label} rate/quota. Switch: {', '.join(FALLBACK_MODELS[1:4])}.\n"
            f"DELEGATE: {label}\n"
            f"TASK: none"
        )
    if working and not at_prompt:
        return (
            f"АНАЛИЗ: {label} активно работает\n"
            f"СОСТОЯНИЕ: working\n"
            f"РЕШЕНИЕ: NO ACTION\n"
            f"DELEGATE: {label}\n"
            f"TASK: none"
        )
    if at_prompt and has_result:
        snippet = log.strip()[-400:].replace("\n", " ")
        return (
            f"АНАЛИЗ: {label} завершил задачу, на промпте\n"
            f"СОСТОЯНИЕ: idle_with_result\n"
            f"РЕШЕНИЕ: REPORT TO MASTER\n"
            f"ОТЧЕТ ДЛЯ МАСТЕРА: {label} idle после работы. Выжимка: {snippet}\n"
            f"DELEGATE: {label}\n"
            f"TASK: none"
        )
    if at_prompt:
        extra = " (контекст высокий CH8x/CH9x — /new)" if high_ctx else ""
        if high_ctx:
            return (
                f"АНАЛИЗ: {label} idle, контекст высокий{extra}\n"
                f"СОСТОЯНИЕ: idle_high_ctx\n"
                f"РЕШЕНИЕ: REPORT TO MASTER\n"
                f"ОТЧЕТ ДЛЯ МАСТЕРА: {label} high context — recommend /new before next task.\n"
                f"DELEGATE: {label}\n"
                f"TASK: none"
            )
        return (
            f"АНАЛИЗ: {label} ждёт задачу на промпте{extra}\n"
            f"СОСТОЯНИЕ: idle\n"
            f"РЕШЕНИЕ: NO ACTION\n"
            f"DELEGATE: {label}\n"
            f"TASK: none"
        )
    if err:
        return (
            f"АНАЛИЗ: {label} ошибка в логе\n"
            f"СОСТОЯНИЕ: error\n"
            f"РЕШЕНИЕ: REPORT TO MASTER\n"
            f"ОТЧЕТ ДЛЯ МАСТЕРА: {label} error в выводе. Проверь pane read.\n"
            f"DELEGATE: {label}\n"
            f"TASK: none"
        )
    return (
        f"АНАЛИЗ: {label} состояние неясно\n"
        f"СОСТОЯНИЕ: unknown\n"
        f"РЕШЕНИЕ: NO ACTION\n"
        f"DELEGATE: {label}\n"
        f"TASK: none"
    )

def read_pane_output(pane_id, lines=25):
    raw = run_herdr_cmd(["pane", "read", pane_id, "--lines", str(lines)])
    if not raw:
        return ""
    try:
        data = json.loads(raw)
        return data.get("result", {}).get("read", {}).get("text", "")
    except Exception:
        return raw

def restart_agent_session(pane_id, label):
    """Принудительно очищает терминал и запускает сессию заново."""
    lab_l = (label or "").lower()
    # orfree: НЕ поднимать interactive pi (tools ломаются). Оставить PS + подсказку.
    if "orfree" in lab_l:
        print(f"[{label}] orfree: PS mode (pi -p). Skip interactive restart.")
        run_herdr_cmd(["pane", "send-keys", pane_id, "Ctrl+c", "Ctrl+c"])
        time.sleep(0.5)
        run_herdr_cmd([
            "pane", "send-text", pane_id,
            "Write-Host 'pi-orfree READY (tencent). Tasks: send_orfree_task.ps1' -ForegroundColor Green"
        ])
        time.sleep(0.3)
        run_herdr_cmd(["pane", "send-keys", pane_id, "Return"])
        return

    print(f"[{label}] Поднимаем упавшего агента (перезапуск)...")
    run_herdr_cmd(["pane", "send-keys", pane_id, "Ctrl+c", "Ctrl+c", "Ctrl+c"])
    time.sleep(1)
    run_herdr_cmd(["pane", "send-keys", pane_id, "Return"])
    time.sleep(1)

    # label may be long "pi-orfree (OpenRouter free)" — match by substring
    cmd_text = AGENT_LAUNCH_COMMANDS.get(label)
    if not cmd_text:
        for k, v in AGENT_LAUNCH_COMMANDS.items():
            if k in lab_l or lab_l in k:
                cmd_text = v
                break
    if cmd_text:
        run_herdr_cmd(["pane", "send-text", pane_id, cmd_text])
        time.sleep(1)
        run_herdr_cmd(["pane", "send-keys", pane_id, "Return"])
        print(f"[{label}] Команда запуска отправлена успешно.")
    else:
        print(f"[Error] Нет конфигурации запуска для агента {label}")

def check_herd_health():
    # Reload anti-spam fingerprints each cycle (file may be updated externally)
    _load_report_state()
    agents = get_herdr_agents()
    if not agents:
        print("[Granite Orchestrator] Herdr panes list is empty.")
        return

    for agent in agents:
        label = agent.get("label") or agent.get("name") or "unknown"
        name = agent.get("name") or ""
        pane_id = agent.get("pane_id")
        status = agent.get("agent_status") or "unknown"

        if is_orch_or_master_pane(agent):
            continue
        if pane_id == MASTER_PANE_ID:
            continue

        print(f"\n--- [Granite Orchestrator] Анализ агента: {label} ({pane_id}) ---")

        terminal_log = read_pane_output(pane_id, lines=40)
        if not terminal_log.strip():
            print(f"[{label}] Лог пуст. Агент спит или не инициализирован.")
            continue

        prev_log = last_agent_outputs.get(label, "")
        current_clean = terminal_log.strip()
        log_unchanged = current_clean == (prev_log or "").strip()
        at_prompt = "~ (main)" in current_clean
        working_ui = "Working..." in current_clean or status == "working"

        # Idle / stuck counters
        is_no_activity = False
        if log_unchanged and (at_prompt or "ожидает" in current_clean.lower() or len(current_clean) < 200):
            no_activity_count[label] = no_activity_count.get(label, 0) + 1
            if no_activity_count[label] >= 2:
                is_no_activity = True
        else:
            no_activity_count[label] = 0
            reported_no_activity[label] = False

        if working_ui and log_unchanged and not at_prompt:
            stuck_working_count[label] = stuck_working_count.get(label, 0) + 1
        else:
            stuck_working_count[label] = 0
        stuck_working = stuck_working_count.get(label, 0) >= STUCK_WORKING_CYCLES

        last_agent_outputs[label] = current_clean

        # Fake-tool + promised artifact checks
        fake_signals = detect_fake_tool_signals(terminal_log)
        missing = missing_promised_artifacts(terminal_log)
        # grace period for paths just promised
        effective_missing = []
        for p in missing:
            key = f"{label}|{p.lower()}"
            promised_path_count[key] = promised_path_count.get(key, 0) + 1
            if promised_path_count[key] >= PROMISED_PATH_GRACE_CYCLES:
                effective_missing.append(p)
        # reset counters for paths that now exist
        for p in extract_promised_paths(terminal_log):
            if os.path.isfile(p):
                promised_path_count.pop(f"{label}|{p.lower()}", None)

        # Interactive claiming write while tools fake → escalate faster
        if is_interactive_lane(label, name) and fake_signals and stuck_working_count.get(label, 0) >= FAKE_TOOL_CYCLES:
            stuck_working = True

        # PS crash
        if "PS C:\\Users" in terminal_log and "~ (main)" not in terminal_log and "pi.ps1" not in terminal_log:
            if is_orfree_lane(label, name):
                print(f"[{label}] PS console — OK for orfree (pi -p). No restart.")
            else:
                print(f"[{label}] Обнаружено падение процесса pi обратно в PowerShell!")
                restart_agent_session(pane_id, label)
            continue

        # Idle watchdog >3 min — soft notify only (no spam Ctrl+C on healthy idle prompt)
        if no_activity_count.get(label, 0) >= 12 and at_prompt:
            if not reported_no_activity.get(label):
                idle_msg = f"Агент {label} idle >3 мин (watchdog, waiting for task)."
                print(f"[{label}] {idle_msg}")
                append_outbox(label, idle_msg, kind="watchdog")
                reported_no_activity[label] = True
            no_activity_count[label] = 0
            continue

        if is_no_activity and not reported_no_activity.get(label) and at_prompt:
            print(f"[{label}] ОБНАРУЖЕНО ОТСУТСТВИЕ АКТИВНОСТИ (ждёт задачу).")
            reported_no_activity[label] = True

        fp = stable_result_fingerprint(label, terminal_log)
        already_reported = reported_result_hash.get(label) == fp

        if is_no_activity and already_reported and not effective_missing and not fake_signals:
            print(f"[{label}] idle + RESULT already reported — skip")
            continue
        if already_reported and ("RESULT:" in terminal_log.upper()) and not effective_missing and not stuck_working:
            print(f"[{label}] same RESULT fingerprint — NO ACTION")
            continue

        # PRIMARY: rule-based (fast, no heartbeat block)
        analysis_result = rule_based_analysis(
            label, terminal_log, status,
            stuck_working=stuck_working,
            fake_signals=fake_signals if (stuck_working or effective_missing or working_ui) else [],
            missing_paths=effective_missing,
        )
        # Optional LLM only when ambiguous + enabled
        if USE_LLM_ANALYSIS and "неясно" in analysis_result:
            log_snippet = terminal_log[-LOG_TRUNCATE_CHARS:]
            llm_out = query_granite(
                f"Monitor herdr agent. Format: АНАЛИЗ/СОСТОЯНИЕ/РЕШЕНИЕ/DELEGATE/TASK.\n"
                f"Rules: Working→NO ACTION; idle no RESULT→NO ACTION; new RESULT→REPORT TO MASTER; "
                f"fake XML tools→INTERRUPT; PS crash→RESTART (except orfree).\n"
                f"Agent={label} status={status}\nLog:\n{log_snippet}"
            )
            if llm_out:
                analysis_result = llm_out
                print(f"[{label}] LLM analysis used")
        print(analysis_result)

        analysis_upper = analysis_result.upper()

        # Actions: interrupt fake/stuck BEFORE report
        if "РЕШЕНИЕ: INTERRUPT_FAKE_TOOL" in analysis_result or "РЕШЕНИЕ: INTERRUPT_STUCK" in analysis_result:
            reason = "fake_tool" if "FAKE" in analysis_upper else "stuck_working"
            detail = ",".join(fake_signals) if fake_signals else reason
            if effective_missing:
                detail += " missing=" + ";".join(effective_missing[:2])
            interrupt_agent(pane_id, label, detail)
            stuck_working_count[label] = 0
            report_problem_to_master(label, reason, detail)
            # mark fingerprint so we don't re-report forever
            reported_result_hash[label] = fp
            _save_report_state()
            continue

        if "ОТЧЕТ ДЛЯ МАСТЕРА" in analysis_upper or "РЕШЕНИЕ: REPORT TO MASTER" in analysis_upper:
            try:
                if already_reported and "missing_artifact" not in analysis_result and "rate_limited" not in analysis_result:
                    print(f"[{label}] REPORT suppressed — fingerprint already sent.")
                else:
                    lines = analysis_result.split("\n")
                    report_line = None
                    for l in lines:
                        if "ОТЧЕТ ДЛЯ МАСТЕРА" in l.upper() or "REPORT TO MASTER" in l.upper():
                            if "РЕШЕНИЕ:" in l.upper():
                                continue
                            report_line = l
                            break
                    if not report_line:
                        for line in (terminal_log or "").splitlines():
                            if "RESULT:" in line.upper():
                                report_line = f"ОТЧЕТ ДЛЯ МАСТЕРА: {label} {line.strip()[:200]}"
                                break
                    if not report_line:
                        for l in lines:
                            if l.strip().upper().startswith("АНАЛИЗ:"):
                                report_line = f"ОТЧЕТ ДЛЯ МАСТЕРА: {label} {l.split(':',1)[-1].strip()[:220]}"
                                break
                        if not report_line:
                            report_line = f"ОТЧЕТ ДЛЯ МАСТЕРА: {label} status={status} (детали в pane {pane_id})"

                    report_content = report_line
                    for prefix in ["ОТЧЕТ ДЛЯ МАСТЕРА:", "ОТЧЕТ ДЛЯ МАСТЕРА", "REPORT TO MASTER:", "REPORT TO MASTER"]:
                        if report_content.upper().startswith(prefix.upper()):
                            report_content = report_content[len(prefix):].strip()
                            break
                    if "см. анализ" in report_content.lower():
                        report_content = f"{label} status={status}; fp={fp[:80]}"

                    reported_result_hash[label] = fp
                    _save_report_state()
                    print(f"[{label}] Отправка отчета мастер-агенту (fp={fp[:60]})...")
                    disp = worker_display_name(label, name)
                    run_herdr_cmd([
                        "pane", "report-metadata", MASTER_PANE_ID,
                        "--source", pane_id,
                        "--display-agent", disp,
                        "--custom-status", report_content[:120]
                    ])
                    run_herdr_cmd([
                        "notification", "show", f"Агент {label} готов!",
                        "--body", report_content[:120],
                        "--sound", "done"
                    ])
                    deliver_report_to_master(label, report_content[:400])
            except Exception as ex:
                print(f"[Error] Не удалось передать отчет мастеру: {ex}")

        if "РЕШЕНИЕ: RESTART" in analysis_result:
            if is_orfree_lane(label, name):
                print(f"[{label}] RESTART suppressed (orfree = pi -p / PS mode)")
            else:
                restart_agent_session(pane_id, label)
        elif "РЕШЕНИЕ: PRESS ENTER" in analysis_result:
            print(f"[{label}] Действие: Отправка Return...")
            run_herdr_cmd(["pane", "send-keys", pane_id, "Return"])

        # DELEGATE only with explicit TASK (never invent)
        if "РЕШЕНИЕ: DELEGATE" in analysis_result and "DELEGATE:" in analysis_result:
            try:
                lines = analysis_result.split("\n")
                delegate_line = [l for l in lines if "DELEGATE:" in l][0]
                target = delegate_line.split("DELEGATE:", 1)[1].strip()
                task_lines = [l for l in lines if l.strip().startswith("TASK:")]
                task = task_lines[0].split("TASK:", 1)[1].strip() if task_lines else ""
                if not task or task.lower() in ("none", "n/a", "-", "нет"):
                    print(f"[{label}] DELEGATE пропущен (TASK пустой/none).")
                else:
                    # Tool-ish tasks: prefer cerebras → mistral → orfree (never interactive hy3)
                    toolish = any(x in task.lower() for x in (
                        "write ", "создай файл", "create file", "artifact", "path=",
                        "edit ", "grep ", "bash ", "tool",
                    ))
                    agents_now = get_herdr_agents()
                    target_pane = None
                    if toolish and (
                        is_interactive_lane(label, name)
                        or target.lower() in ("interactive", "hy3-interactive", "pi-orfree")
                    ):
                        target_pane = pick_tool_worker_pane(agents_now)
                        if target_pane:
                            print(f"[{label}] toolish TASK rerouted → tool-worker pane {target_pane} (cerebras/mistral/orfree)")
                    if not target_pane:
                        for a in agents_now:
                            lab = (a.get("label") or "").strip()
                            nm = (a.get("name") or "").strip()
                            ag = (a.get("agent") or "").strip()
                            pid = a.get("pane_id")
                            if target in (lab, nm, ag, pid):
                                target_pane = pid
                                break
                    if not target_pane and target.startswith("w") and ":" in target:
                        target_pane = target
                    if target_pane:
                        print(f"[{label}] Делегирую → pane {target_pane} ({target}): {task[:50]}...")
                        run_herdr_cmd(["agent", "send", target_pane, task])
                        time.sleep(0.3)
                        run_herdr_cmd(["pane", "send-keys", target_pane, "Return"])
                        print(f"[{label}] Задача отправлена с Return.")
                    else:
                        print(f"[{label}] DELEGATE fail: target '{target}' not found in panes")
            except Exception as ex:
                print(f"[Error] Не удалось делегировать: {ex}")

def worker_display_name(lab, name=""):
    """Stable short names matching pane labels (model-first)."""
    s = f"{lab or ''} {name or ''}".lower()
    if "orfree" in s:
        return "hy3-orfree"
    if "cerebras" in s:
        return "cerebras gpt-oss"
    if "mistral" in s:
        return "mistral-small"
    if "groq" in s:
        return "groq llama-3.3"
    if "nemo" in s:
        return "nemotron-super free"
    if "interactive" in s or "tencet" in s or "tencet-2" in s:
        return "hy3-interactive"
    # bare tencent-hy3 #N worker (not orch)
    if "tencent" in s or "hy3" in s:
        if "orch" in s or "granite" in s:
            return "orch-hy3"
        if "#" in s or "worker" in s or "pi-" in s:
            return "hy3-interactive"
    if "orch" in s or "granite" in s:
        return "orch-hy3"
    if "grok" in s or "agy" in s or "master" in s:
        return "grok-master"
    if "pi-" in s or (name or "").lower().startswith("pi"):
        return (name or lab or "pi-worker")[:28]
    # fallback: compress label
    lab = (lab or name or "?").replace("tencent/", "").replace(" · ", "-")
    return lab[:28]


def herd_status_snapshot():
    """Compact one-line status of worker panes only (no orch/master noise)."""
    agents = get_herdr_agents()
    parts = []
    for a in agents:
        if is_orch_or_master_pane(a):
            continue
        lab = a.get("label") or a.get("name") or "?"
        name = a.get("name") or ""
        combined = f"{lab} {name}".lower()
        short = worker_display_name(lab, name)
        if short in ("orch-hy3", "grok-master"):
            continue
        st = (a.get("agent_status") or "unknown").lower()
        agent_kind = (a.get("agent") or "").lower()
        # orfree: idle/unknown = READY (pi -p worker lane)
        if "orfree" in combined:
            if st in ("unknown", "", "idle"):
                st = "ready"
        elif st in ("unknown", ""):
            if agent_kind == "pi" or "pi" in combined or "hy3" in combined or "tencent" in combined or "groq" in combined or "cerebras" in combined:
                st = "idle"
            else:
                continue
        parts.append(f"{short}={st}")
    return ", ".join(parts) if parts else "no workers"


_last_heartbeat_ts = 0
_last_heartbeat_snap = None
HEARTBEAT_SEC = 60  # file/badge every 60s; snap change = immediate


def maybe_heartbeat_to_master(iteration, force=False):
    """Снимок с timestamp (screen) для master — очерёдность и устаревание."""
    global _last_heartbeat_ts, _last_heartbeat_snap
    now = time.time()
    snap = herd_status_snapshot()
    snap_changed = snap != _last_heartbeat_snap
    # Always force when workers appear after "no workers"
    if _last_heartbeat_snap == "no workers" and snap != "no workers":
        force = True
    if not force and not snap_changed and (now - _last_heartbeat_ts < HEARTBEAT_SEC):
        return
    # During cold start: still write status file, but do not chat-push "no workers"
    cold = is_cold_start()
    skip_chat = cold and snap == "no workers"

    ts = now_iso()
    unix = now_unix()
    msg = f"heartbeat #{iteration}: {snap}"
    if cold:
        msg += " [cold-start]"
    print(f"[Heartbeat] ts={ts} {msg}")
    rec = append_outbox("orch-heartbeat", f"ts={ts} unix={unix} | {msg}", kind="heartbeat")
    write_status_screen(extra_event=rec)
    try:
        run_herdr_cmd([
            "pane", "report-metadata", MASTER_PANE_ID,
            "--source", MASTER_PANE_ID,
            "--display-agent", "orch",
            "--custom-status", f"{ts[-8:]} {snap}"[:120],
        ])
    except Exception:
        pass
    # Chat push only when useful: not cold no-workers; prefer snap change or periodic
    if (
        MASTER_PUSH_SCREEN_WHEN_IDLE
        and get_master_status() == "idle"
        and not skip_chat
        and (force or snap_changed or (now - _last_heartbeat_ts >= HEARTBEAT_SEC))
    ):
        line = (
            f"[orch-screen ts={ts} unix={unix} seq={rec.get('seq') if rec else '?'}] "
            f"{snap} | orfree=pi-p; interactive=chat; tools≠hy3-interactive"
        )
        run_herdr_cmd(["agent", "send", MASTER_PANE_ID, line])
        time.sleep(0.25)
        run_herdr_cmd(["pane", "send-keys", MASTER_PANE_ID, "Return"])
    _last_heartbeat_ts = now
    _last_heartbeat_snap = snap


def main():
    global _orch_started_at
    _orch_started_at = time.time()
    print(f"Запуск глубокого Granite-оркестратора с автоматическим подъёмом ({MODEL_NAME})...")
    print(f"Политика: rule-first USE_LLM={USE_LLM_ANALYSIS}; interactive=chat; tools→orfree/pi -p")
    print(f"Анализ каждые {CHECK_INTERVAL_SEC}s | stuck≥{STUCK_WORKING_CYCLES}cyc | cold_start={COLD_START_SEC}s")
    print(f"Status screen: {ORCH_STATUS_LATEST} (+ .md)")
    print(f"Outbox: {ORCH_OUTBOX} (seq+ts for order)")
    print(f"MASTER_INJECT_CHAT={MASTER_INJECT_CHAT} PUSH_WHEN_IDLE={MASTER_PUSH_SCREEN_WHEN_IDLE}")
    print(f"Fallbacks: {FALLBACK_MODELS}")
    _load_report_state()
    _ensure_outbox_seq()
    print(f"[Orchestrator] loaded {len(reported_result_hash)} fingerprints; outbox_seq={_outbox_seq}")

    # Brief settle so workers registered before first snapshot (anti race "no workers")
    print(f"[Orchestrator] cold-start settle 5s...")
    time.sleep(5)
    maybe_heartbeat_to_master(0, force=True)

    iteration = 0
    while True:
        try:
            # Heartbeat FIRST (cheap) so status never stale during analysis
            maybe_heartbeat_to_master(iteration, force=False)

            if iteration % 20 == 0:
                print("[Orchestrator] Запуск фонового OCR сканирования новых изображений...")
                try:
                    subprocess.Popen(
                        ["node", "C:/Users/anton/agent_tools/ocr_watcher.js"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                except Exception as ex:
                    print(f"[Error] Не удалось запустить OCR watcher: {ex}")

            check_herd_health()
            # Post-analysis snap (catch worker state changes during cycle)
            maybe_heartbeat_to_master(iteration, force=False)
            iteration += 1
        except KeyboardInterrupt:
            print("\nОркестратор остановлен.")
            sys.exit(0)
        except Exception as e:
            print(f"Ошибка диспетчера: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

        time.sleep(CHECK_INTERVAL_SEC)

if __name__ == "__main__":
    main()
