# Step = Commit protocol (ik / mesh work)

**Rule:** after every completed implementation step, create a **git commit in `C:\Users\anton\Sync`** so we can roll back.

## Rules
1. **Repo:** only `C:\Users\anton\Sync` (never `C:\Users\anton` root).
2. **One step → one commit** with message: `step N: <what>` or `feat(ik): <what>`.
3. **Selective stage** — do **not** `git add -A` while the tree is dirty with emails/auth/locks.
4. **No secrets:** tokens, `apiKey`, `.baileys_auth`, `*_token.json`, locks, feeds.
5. Prefer staging explicit paths: `Configs/pi/`, `skills/…`, `Scripts/ik_*`, `Docs/…`.
6. After commit: note hash in chat + optional wiki raw one-liner.
7. **Do not force-push** without user confirm.

## Example
```powershell
cd C:\Users\anton\Sync
git add Docs/IK_HERD_DESIGN.md Configs/pi/model_pool.json Scripts/ik_model_probe.py
git status --short
git commit -m "step 1: model_pool.json + probe script"
git log -1 --oneline
```

## Rollback
```powershell
git log --oneline -20
git revert <hash>   # preferred
# or: git checkout <hash> -- path/to/file
```
