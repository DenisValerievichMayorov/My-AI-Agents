# Browser VERIFY (CDP smoke)

Канон: AGENTS.md §7 (CDP profile) + §12.2 (VERIFY table).

## When required

- Playwright / Puppeteer / any browser automation
- Web scraper tasks
- UI or dashboard changes that must be visible in browser
- User said «проверь в браузере» / open page / click flow

## Pass criteria (minimum)

1. **CDP reachable**
   ```powershell
   Invoke-RestMethod http://localhost:9222/json/version
   ```
   Expect JSON with `Browser` / `webSocketDebuggerUrl`.

2. **Connect, don't launch**
   ```javascript
   const browser = await chromium.connectOverCDP('http://localhost:9222');
   const context = browser.contexts()[0];
   const page = context.pages()[0] || await context.newPage();
   ```
   Forbidden for standard tasks: `chromium.launch()`, empty `newContext()` (cookie loss).

3. **One observable fact in VERIFY**
   - `title` of page, or
   - visible text / selector count, or
   - HTTP status / network response relevant to task

## VERIFY line examples

```text
VERIFY: browser-smoke GET :9222/json/version → Browser=Chrome/1xx; page https://example.com title="Example" → OK
VERIFY: FAIL CDP:9222 offline (connection refused); not done
VERIFY: N/A no UI (CLI-only script change)
```

## Offline fallback

If CDP is down:

1. Prefer: fix/start Chrome with remote debugging on 9222 (user or orchestrator).
2. Or report `VERIFY: FAIL CDP offline; not done`.
3. `N/A` only with explicit reason **and** user accept of fallback (e.g. API-only check).

## Smoke script

```powershell
powershell -File C:/Users/anton/Sync/skills/mesh-quality-gate/scripts/browser-cdp-smoke.ps1
# optional: -Url "https://example.com"  (requires Playwright; default is CDP version only)
```
