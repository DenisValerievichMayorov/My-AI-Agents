# Orchestrator task brief (copy to agent)

```text
GOAL: <one sentence outcome>
SCOPE_PATH: <absolute or repo-relative path agent may write>
BRANCH_OR_WORKTREE: <branch name or worktree path or "single-cwd">
OUT_OF_SCOPE: <paths/actions forbidden>
DoD:
  - <acceptance criterion 1>
  - <acceptance criterion 2>
VERIFY:
  - <exact checks expected, e.g. "npm test", "node scripts/lint.js">
  - <if UI: browser-smoke CDP :9222 + observable page fact>
MODEL_HINT: plan | implement | review | explore
REVIEW_REQUIRED: <yes if ≥2 files or security/money/mail-WA/shutdown | no>
REVIEWER: <agent or "master+check-work" | n/a>
REPORT_TO: <agy-main | grok | mesh | wiki/raw/agent_logs.md>
CONTEXT: <links to wiki pages, tickets, prior reports>
```

## Decomposition rule

If estimate >30 minutes → split into 2–4 briefs with separate SCOPE when possible.

## Defaults (P0)

- ≥2 tracked files → REVIEW_REQUIRED=yes, separate Author ≠ Reviewer.
- UI/scraper → VERIFY must include browser-smoke (not chromium.launch).
