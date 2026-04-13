import { readFileSync, writeFileSync, renameSync, existsSync } from 'fs';
import { join } from 'path';
import { getScriptDir } from './utils.ts';

export interface IssueState {
  status: 'not-ready' | 'implementing' | 'implemented' | 'failed';
  prNumber?: number;
  branchName?: string;
  processedAt: string;
}

export interface PRState {
  issueNumber: number;
  lastCheckedAt: string;
  lastCommentId: number;
}

export interface State {
  lastRun: string;
  issues: Record<number, IssueState>;
  prs: Record<number, PRState>;
}

const __dir = getScriptDir(import.meta.url);
const STATE_PATH = join(__dir, 'state.json');
const STATE_TMP = join(__dir, 'state.json.tmp');

export function loadState(): State {
  if (!existsSync(STATE_PATH)) {
    return { lastRun: '', issues: {}, prs: {} };
  }
  let state: State;
  try {
    state = JSON.parse(readFileSync(STATE_PATH, 'utf-8'));
  } catch {
    console.warn('Warning: state.json is corrupt, starting fresh');
    return { lastRun: '', issues: {}, prs: {} };
  }
  // Recover stale 'implementing' entries from a crashed previous run
  for (const [num, entry] of Object.entries(state.issues)) {
    if (entry.status === 'implementing') {
      console.warn(`  Recovering stale 'implementing' state for issue #${num} → failed`);
      entry.status = 'failed';
    }
  }
  return state;
}

export function saveState(state: State): void {
  writeFileSync(STATE_TMP, JSON.stringify(state, null, 2));
  renameSync(STATE_TMP, STATE_PATH);
}
