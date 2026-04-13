import { execFileSync } from 'child_process';

export interface Issue {
  number: number;
  title: string;
  body: string;
  labels: Array<{ name: string }>;
  user: { login: string };
}

export interface PRComment {
  id: number;
  body: string;
  user: { login: string };
  created_at: string;
}

export function listOpenIssues(repo: string): Issue[] {
  const raw = execFileSync('gh', [
    'issue', 'list',
    '--repo', repo,
    '--state', 'open',
    '--json', 'number,title,body,labels,author',
    '--limit', '100',
  ], { encoding: 'utf-8' });

  // gh uses 'author' in issue list, normalize to 'user'
  return JSON.parse(raw).map((issue: Record<string, unknown>) => ({
    ...issue,
    user: (issue.author as { login: string }) ?? { login: 'unknown' },
  }));
}

export function isCollaborator(repo: string, username: string): boolean {
  try {
    execFileSync('gh', ['api', `repos/${repo}/collaborators/${username}`], {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return true;
  } catch {
    return false;
  }
}

export function postComment(repo: string, issueNumber: number, body: string): void {
  execFileSync('gh', ['issue', 'comment', String(issueNumber), '--repo', repo, '--body', body]);
}

export function listPRCommentsSince(repo: string, prNumber: number, since: string): PRComment[] {
  try {
    const raw = execFileSync('gh', [
      'api', `repos/${repo}/pulls/${prNumber}/comments?since=${encodeURIComponent(since)}`,
    ], { encoding: 'utf-8' });
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

export function getPRBranch(repo: string, prNumber: number): string {
  const raw = execFileSync('gh', [
    'api', `repos/${repo}/pulls/${prNumber}`,
    '--jq', '.head.ref',
  ], { encoding: 'utf-8' });
  return raw.trim();
}
