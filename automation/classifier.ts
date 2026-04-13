import { execFileSync } from 'child_process';
import type { Issue } from './github.ts';
import type { Config } from './config.ts';

export interface ClassificationResult {
  ready: boolean;
  reasoning: string;
}

export async function classifyIssue(issue: Issue, config: Config): Promise<ClassificationResult> {
  const criteria = config.readinessCriteria.map((c, i) => `${i + 1}. ${c}`).join('\n');

  const prompt = `You are a GitHub issue readiness classifier for a threat hunting framework repository.

Evaluate whether this issue has enough information to be automatically implemented.

Readiness criteria (ALL must be met for ready=true):
${criteria}

Respond with ONLY a valid JSON object — no markdown, no explanation, no prose:
{"ready": boolean, "reasoning": "one concise sentence explaining your decision"}

---BEGIN ISSUE DATA---
Issue #${issue.number}: ${issue.title}

${issue.body?.trim() || '(no body provided)'}
---END ISSUE DATA---`;

  try {
    const output = execFileSync('claude', ['-p', prompt], {
      encoding: 'utf-8',
      timeout: 30_000,
    });

    const match = output.match(/\{[\s\S]*?"ready"[\s\S]*?\}/);
    if (!match) throw new Error(`No JSON found in response: ${output.substring(0, 200)}`);
    return JSON.parse(match[0]);
  } catch (err) {
    console.error(`  Classifier error for issue #${issue.number}:`, err);
    return { ready: false, reasoning: 'Classification failed — manual review required' };
  }
}
