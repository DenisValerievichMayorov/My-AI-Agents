# Mesh report template

```text
TASK: <short-id or title>
AGENT: <grok|pi-orfree|agy|...>
SCOPE: <path> | branch=<name> | worktree=<path>
DONE:
  - <fact 1>
  - <fact 2>
VERIFY:
  - <command> → RC=<n>
  - browser-smoke: <CDP fact or N/A reason>
  - OR N/A (<reason>)
REVIEW: <self-only | pending | pass by <agent> | skip-by-user>
RISK: <none | description>
NEXT: <idle-audit | handoff to X | user decision needed | done>
```

## Rules

- Max ~15 lines in mesh chat; long logs → file path under DONE/VERIFY.
- No "готово" without VERIFY line.
- ≥2 tracked-files → REVIEW cannot stay empty; need pass or skip-by-user.
- UI/web work → browser-smoke line required (CDP :9222).
- Russian preferred for human-facing summaries; commands/paths stay literal.
