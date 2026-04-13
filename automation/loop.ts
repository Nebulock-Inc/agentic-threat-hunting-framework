import { loadConfig } from './config.ts';
import { loadState, saveState } from './state.ts';
import {
  listOpenIssues,
  isCollaborator,
  postComment,
  listPRCommentsSince,
  getPRBranch,
} from './github.ts';
import { classifyIssue } from './classifier.ts';
import { implement, implementFeedback } from './implementer.ts';

const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run');
const watchMode = args.includes('--watch');

async function runCycle(config: ReturnType<typeof loadConfig>): Promise<void> {
  const state = loadState();
  const now = new Date().toISOString();
  const collaboratorCache = new Map<string, boolean>();

  console.log(`\n[${now}] Starting cycle | repo: ${config.repo}${dryRun ? ' | DRY RUN' : ''}`);

  // ── Phase 1: Classify and implement new issues ──────────────────────────

  let issues;
  try {
    issues = listOpenIssues(config.repo);
  } catch (err) {
    console.error('Failed to fetch issues:', err);
    return;
  }

  console.log(`Found ${issues.length} open issue(s)`);

  for (const issue of issues) {
    const existing = state.issues[issue.number];
    if (existing) {
      console.log(`  #${issue.number}: skip (${existing.status})`);
      continue;
    }

    // Security layer 1: label gate
    const labeled = issue.labels.some(l => l.name === config.triggerLabel);
    if (!labeled) {
      console.log(`  #${issue.number}: no '${config.triggerLabel}' label — skip`);
      continue;
    }

    // Security layer 2: collaborator check (cached per cycle)
    const login = issue.user.login;
    if (config.requireCollaborator) {
      if (!collaboratorCache.has(login)) {
        collaboratorCache.set(login, dryRun || isCollaborator(config.repo, login));
      }
      if (!collaboratorCache.get(login)) {
        console.log(`  #${issue.number}: '${login}' is not a collaborator — skip`);
        continue;
      }
    }

    console.log(`  #${issue.number}: "${issue.title}" — classifying...`);
    const classification = await classifyIssue(issue, config);
    console.log(`  #${issue.number}: ${classification.ready ? 'READY ✓' : 'NOT READY ✗'} — ${classification.reasoning}`);

    if (!classification.ready) {
      const comment = config.draftCommentTemplate.replace('{reasoning}', classification.reasoning);
      if (!dryRun) postComment(config.repo, issue.number, comment);
      else console.log(`  [DRY RUN] Would post not-ready comment to #${issue.number}`);
      state.issues[issue.number] = { status: 'not-ready', processedAt: now };
      saveState(state);
      continue;
    }

    state.issues[issue.number] = { status: 'implementing', processedAt: now };
    saveState(state);

    try {
      const { branchName, prNumber } = implement(issue, config, dryRun);
      state.issues[issue.number] = { status: 'implemented', prNumber, branchName, processedAt: now };
      if (prNumber > 0) {
        state.prs[prNumber] = { issueNumber: issue.number, lastCheckedAt: now, lastCommentId: 0 };
      }
      console.log(`  #${issue.number}: implemented → ${branchName}${prNumber ? ` / PR #${prNumber}` : ''}`);
    } catch (err) {
      console.error(`  #${issue.number}: implementation failed:`, err);
      state.issues[issue.number] = { status: 'failed', processedAt: now };
    }

    saveState(state);
  }

  // ── Phase 2: Handle PR review comments ─────────────────────────────────

  const prEntries = Object.entries(state.prs);
  if (prEntries.length > 0) {
    console.log(`\nChecking ${prEntries.length} tracked PR(s)...`);
  }

  for (const [prNumStr, prState] of prEntries) {
    const prNumber = parseInt(prNumStr);
    const newComments = dryRun
      ? []
      : listPRCommentsSince(config.repo, prNumber, prState.lastCheckedAt);

    if (newComments.length === 0) {
      console.log(`  PR #${prNumber}: no new comments`);
      continue;
    }

    console.log(`  PR #${prNumber}: ${newComments.length} new comment(s) — implementing feedback...`);

    try {
      const branch = getPRBranch(config.repo, prNumber);
      implementFeedback(prNumber, branch, newComments, config, dryRun);
      prState.lastCheckedAt = now;
      prState.lastCommentId = Math.max(...newComments.map(c => c.id));
      saveState(state);
    } catch (err) {
      console.error(`  PR #${prNumber}: feedback failed:`, err);
    }
  }

  state.lastRun = now;
  saveState(state);
  console.log(`[${new Date().toISOString()}] Cycle complete.\n`);
}

async function main(): Promise<void> {
  const config = loadConfig();

  if (watchMode) {
    const intervalMs = config.intervalMinutes * 60_000;
    console.log(`ATHF Automation Loop | daemon mode | interval: ${config.intervalMinutes} min`);
    await runCycle(config);
    setInterval(() => runCycle(config), intervalMs);
  } else {
    await runCycle(config);
    process.exit(0);
  }
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
