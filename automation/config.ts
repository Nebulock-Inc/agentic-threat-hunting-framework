import { readFileSync } from 'fs';
import { join } from 'path';
import { getScriptDir } from './utils.ts';

export interface Config {
  repo: string;
  repoPath: string;
  intervalMinutes: number;
  triggerLabel: string;
  requireCollaborator: boolean;
  readinessCriteria: string[];
  draftCommentTemplate: string;
}

const __dir = getScriptDir(import.meta.url);

export function loadConfig(): Config {
  const configPath = join(__dir, 'config.json');
  let raw: string;
  try {
    raw = readFileSync(configPath, 'utf-8');
  } catch {
    console.error(`Config not found at: ${configPath}`);
    console.error('Copy automation/config.example.json → automation/config.json and fill in repoPath.');
    process.exit(1);
  }
  const parsed = JSON.parse(raw);
  delete parsed._comment;
  return parsed as Config;
}
