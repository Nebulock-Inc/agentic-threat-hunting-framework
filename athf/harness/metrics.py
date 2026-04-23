"""Score aggregation and report rendering for harness evaluation."""

import json
from dataclasses import dataclass, field
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from athf.harness.dataset import EvalDataset
from athf.harness.evaluator import CaseResult


@dataclass
class HarnessReport:
    """Aggregated harness evaluation report."""

    agent_name: str
    dataset_name: str
    total_cases: int
    passed: int
    failed: int
    pass_rate: float
    avg_score: float
    case_results: List[CaseResult] = field(default_factory=list)

    @property
    def all_violations(self) -> List[str]:
        violations = []
        for r in self.case_results:
            for v in r.violations:
                violations.append("[{}] {}".format(r.case_id, v))
        return violations

    @property
    def all_warnings(self) -> List[str]:
        warnings = []
        for r in self.case_results:
            for w in r.warnings:
                warnings.append("[{}] {}".format(r.case_id, w))
        return warnings


def build_report(
    agent_name: str,
    dataset: EvalDataset,
    results: List[CaseResult],
) -> HarnessReport:
    """Build a HarnessReport from case results.

    Args:
        agent_name: Name of the agent evaluated.
        dataset: The eval dataset used.
        results: List of CaseResult from the evaluator.

    Returns:
        HarnessReport with aggregated metrics.
    """
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    pass_rate = round(passed / total, 3) if total > 0 else 0.0
    avg_score = round(sum(r.score for r in results) / total, 3) if total > 0 else 0.0

    return HarnessReport(
        agent_name=agent_name,
        dataset_name=dataset.description or dataset.agent,
        total_cases=total,
        passed=passed,
        failed=failed,
        pass_rate=pass_rate,
        avg_score=avg_score,
        case_results=results,
    )


def render_report_table(report: HarnessReport, console: Console) -> None:
    """Render a harness report as a Rich table.

    Args:
        report: The harness report to render.
        console: Rich Console to print to.
    """
    pass_color = "green" if report.pass_rate == 1.0 else ("yellow" if report.pass_rate >= 0.5 else "red")
    score_color = "green" if report.avg_score >= 0.8 else ("yellow" if report.avg_score >= 0.5 else "red")

    # Summary panel
    summary = (
        "Agent: [bold]{agent}[/bold]   "
        "Dataset: [dim]{dataset}[/dim]   "
        "Cases: {total}   "
        "Pass Rate: [{pc}]{passed}/{total}  ({rate:.0%})[/{pc}]   "
        "Avg Score: [{sc}]{score:.2f}[/{sc}]"
    ).format(
        agent=report.agent_name,
        dataset=report.dataset_name,
        total=report.total_cases,
        passed=report.passed,
        rate=report.pass_rate,
        pc=pass_color,
        score=report.avg_score,
        sc=score_color,
    )
    console.print(Panel(summary, title="[bold]Harness Eval Report[/bold]", expand=False))

    # Case table
    table = Table(show_header=True, header_style="bold cyan", expand=False)
    table.add_column("Case", style="dim", width=8)
    table.add_column("Description", min_width=30)
    table.add_column("Status", width=8)
    table.add_column("Score", width=7, justify="right")

    for result in report.case_results:
        if result.error:
            status = "[red]ERROR[/red]"
            score_str = "[red]—[/red]"
        elif result.passed:
            status = "[green]PASS[/green]"
            score_str = "[green]{:.2f}[/green]".format(result.score)
        else:
            status = "[red]FAIL[/red]"
            score_str = "[red]{:.2f}[/red]".format(result.score)

        table.add_row(result.case_id, result.description, status, score_str)

    console.print(table)

    # Violations
    violations = report.all_violations
    if violations:
        console.print("\n[bold red]Violations:[/bold red]")
        for v in violations:
            console.print("  [red]✗[/red] {}".format(v))

    # Warnings
    warnings = report.all_warnings
    if warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for w in warnings:
            console.print("  [yellow]⚠[/yellow] {}".format(w))


def render_report_json(report: HarnessReport) -> str:
    """Render a harness report as a JSON string.

    Args:
        report: The harness report to serialize.

    Returns:
        JSON string.
    """
    cases = []
    for r in report.case_results:
        cases.append(
            {
                "case_id": r.case_id,
                "description": r.description,
                "passed": r.passed,
                "score": r.score,
                "violations": r.violations,
                "warnings": r.warnings,
                "error": r.error,
            }
        )

    data = {
        "agent_name": report.agent_name,
        "dataset_name": report.dataset_name,
        "total_cases": report.total_cases,
        "passed": report.passed,
        "failed": report.failed,
        "pass_rate": report.pass_rate,
        "avg_score": report.avg_score,
        "cases": cases,
    }
    return json.dumps(data, indent=2)
