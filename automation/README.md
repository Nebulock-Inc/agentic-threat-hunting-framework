# ATHF Automation Loop

A local TypeScript daemon that polls GitHub Issues every 15 minutes, classifies them with Claude, autonomously implements ready issues into branches/PRs, and handles PR review feedback.

## Security Model

**Only trusted issues are processed.** Three layers of protection:

1. **Label gate** — Issues must have the `auto:ready` label (only collaborators can apply labels)
2. **Collaborator check** — Issue author must have repo write access
3. **Prompt isolation** — Issue bodies are passed as quoted data, not raw instructions

Config and state files are excluded from git (local-only). Never commit `config.json`.

## Setup

### 1. Prerequisites

- `gh` CLI authenticated: `gh auth status`
- `claude` CLI available: `which claude`
- Bun installed: `which bun`

### 2. Configure

```bash
cd automation/
cp config.example.json config.json
```

Edit `config.json`:
- Set `repoPath` to your local clone path
- Adjust `intervalMinutes` if desired
- Customize `readinessCriteria` for your standards

### 3. Create the trigger label on GitHub

```bash
gh label create "auto:ready" --repo Nebulock-Inc/agentic-threat-hunting-framework \
  --color "0075ca" --description "Cleared for automated implementation"
```

### 4. Test with dry-run

```bash
bun run dry-run
# or directly:
bun run loop.ts --dry-run
```

Dry-run mode reads issues and classifies them but posts no comments, creates no branches, and spawns no Claude subagents.

## Running

### One-shot (for cron)

```bash
bun run once
# or:
bun run loop.ts --once
```

### Daemon (long-running process)

```bash
bun run start
# or:
bun run loop.ts --watch
```

### Cron setup (every 15 minutes)

```bash
crontab -e
```

Add:
```
*/15 * * * * cd /path/to/agentic-threat-hunting-framework && /Users/sydney/.bun/bin/bun run automation/loop.ts --once >> automation/loop.log 2>&1
```

## Workflow

```
Every N minutes:
  ├─ Fetch open GitHub issues
  ├─ For each unlabeled/unprocessed issue → skip
  ├─ For each issue with 'auto:ready' label:
  │   ├─ Verify author is repo collaborator
  │   ├─ Classify with Claude → ready / not-ready
  │   ├─ Not-ready → post draft comment (what's missing)
  │   └─ Ready → spawn Claude subagent:
  │       ├─ Create branch: auto/issue-{N}-{slug}
  │       ├─ Activate .venv, read AGENTS.md
  │       ├─ Implement using ATHF CLI conventions
  │       ├─ Run pytest
  │       ├─ Commit + push
  │       └─ Create PR (Closes #N)
  └─ For each tracked PR:
      ├─ Check for new review comments
      └─ If new comments → spawn Claude to implement feedback + push
```

## State

`state.json` (local, never committed) tracks:

```json
{
  "lastRun": "2026-04-13T12:00:00Z",
  "issues": {
    "42": { "status": "implemented", "prNumber": 15, "branchName": "auto/issue-42-add-hunt-template", "processedAt": "..." },
    "43": { "status": "not-ready", "processedAt": "..." }
  },
  "prs": {
    "15": { "issueNumber": 42, "lastCheckedAt": "...", "lastCommentId": 789 }
  }
}
```

Issue statuses: `not-ready` | `implementing` | `implemented` | `failed`

To re-process an issue, remove its entry from `state.json`.

## Files

| File | Purpose |
|---|---|
| `loop.ts` | Main entry point and orchestrator |
| `config.ts` | Config types and loader |
| `state.ts` | Atomic JSON state persistence |
| `github.ts` | `gh` CLI wrappers |
| `classifier.ts` | Claude issue readiness classifier |
| `implementer.ts` | Claude autonomous implementation + PR feedback |
| `config.example.json` | Config template (committed) |
| `config.json` | Your local config (gitignored) |
| `state.json` | Runtime state (gitignored) |
| `loop.log` | Cron output log (gitignored) |
