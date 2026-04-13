import { dirname } from 'path';
import { fileURLToPath } from 'url';
import { execFileSync } from 'child_process';

export function getScriptDir(importMetaUrl: string): string {
  return dirname(fileURLToPath(importMetaUrl));
}

// Safe git wrapper — uses execFileSync with array args (no shell injection risk)
export function gitCmd(repoPath: string, ...args: string[]): string {
  return execFileSync('git', ['-C', repoPath, ...args], {
    encoding: 'utf-8',
    stdio: ['pipe', 'pipe', 'pipe'],
  });
}
