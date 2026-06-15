"""Detection rule evaluation and analysis commands."""

import json
import logging
import signal
import sys
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Setup logging
logger = logging.getLogger("athf.detect")
logger.setLevel(logging.INFO)

# Add file handler if log directory exists
log_dir = Path.home() / ".athf" / "logs"
if log_dir.exists():
    handler = logging.FileHandler(log_dir / "detect.log")
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)
else:
    # Create log directory if it doesn't exist
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_dir / "detect.log")
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
    except Exception:
        # Fall back to console-only logging if directory creation fails
        pass


# Custom Exception Classes
class ClickHouseConnectionError(Exception):
    """Raised when ClickHouse connection fails."""

    pass


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""

    pass


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


class RuleNotFoundError(Exception):
    """Raised when a rule cannot be found."""

    pass


# Type variable for generic function return type
F = TypeVar("F", bound=Callable[..., Any])


def retry_on_transient_error(max_attempts: int = 3, backoff_factor: float = 2.0) -> Callable[[F], F]:
    """Retry on transient errors with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier

    Returns:
        Decorator function
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Don't retry on validation errors or configuration errors
                    if isinstance(e, (ValidationError, ConfigurationError, RuleNotFoundError)):
                        raise

                    if attempt == max_attempts - 1:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}: {e}")
                        raise

                    wait_time = backoff_factor ** attempt
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
            return None  # Should never reach here

        return wrapper  # type: ignore

    return decorator


def validate_config_file(config_path: Optional[Path]) -> None:
    """Validate configuration file exists and is readable.

    Args:
        config_path: Path to configuration file

    Raises:
        ConfigurationError: If config is invalid
    """
    if config_path is None:
        return  # Using default config

    if not config_path.exists():
        raise ConfigurationError(
            f"Configuration file not found: {config_path}\n"
            f"Expected path: {config_path.absolute()}\n"
            f"Create a config file or omit --config to use defaults."
        )

    if not config_path.is_file():
        raise ConfigurationError(
            f"Configuration path is not a file: {config_path}"
        )

    if not config_path.suffix in [".yaml", ".yml"]:
        raise ConfigurationError(
            f"Configuration file must be YAML (.yaml or .yml): {config_path}"
        )

    logger.info(f"Configuration file validated: {config_path}")


def validate_output_directory(output_path: str) -> Path:
    """Validate output directory is writable.

    Args:
        output_path: Output directory path

    Returns:
        Validated Path object

    Raises:
        ValidationError: If directory is not writable
    """
    output_dir = Path(output_path)

    # Check parent directory exists if output doesn't exist yet
    if not output_dir.exists():
        parent = output_dir.parent
        if not parent.exists():
            raise ValidationError(
                f"Parent directory does not exist: {parent}\n"
                f"Create the parent directory first or choose a different output path."
            )

        # Try to create the directory
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")
        except Exception as e:
            raise ValidationError(
                f"Cannot create output directory: {output_dir}\n"
                f"Error: {e}\n"
                f"Check directory permissions."
            )

    # Check directory is writable
    if not output_dir.is_dir():
        raise ValidationError(
            f"Output path is not a directory: {output_dir}"
        )

    # Test write permission
    test_file = output_dir / ".write_test"
    try:
        test_file.touch()
        test_file.unlink()
        logger.info(f"Output directory validated: {output_dir}")
    except Exception as e:
        raise ValidationError(
            f"Output directory is not writable: {output_dir}\n"
            f"Error: {e}\n"
            f"Check directory permissions."
        )

    return output_dir


# Graceful interrupt handler
_interrupted = False


def setup_interrupt_handler() -> None:
    """Setup handler for graceful Ctrl+C interruption."""

    def signal_handler(sig: int, frame: Any) -> None:
        global _interrupted
        _interrupted = True
        console.print("\n\n[yellow]⚠ Interrupt received. Saving partial results...[/yellow]\n")
        logger.warning("User interrupted operation")

    signal.signal(signal.SIGINT, signal_handler)

DETECT_EPILOG = """
\b
Examples:
  # Evaluate top 20 rules with 5 for deep analysis
  athf detect evaluate --top 20 --deep-analysis 5

  # Evaluate specific number of rules
  athf detect evaluate --top 10 --output ./eval-results/

  # Score a specific rule
  athf detect score --rule-name "okta_anomalous_authentication"

  # Review signal distribution
  athf detect review-signals

  # Generate YAML for evaluated rules
  athf detect generate-yaml --input ./results/recommendations.json

\b
Workflow:
  1. Evaluate rules → athf detect evaluate
  2. Review recommendations in output directory
  3. Generate YAML → athf detect generate-yaml
  4. Deploy updated rules to production

\b
Learn more: See investigations/I-0012/scripts/rule_evaluator/README.md
"""


@click.group(epilog=DETECT_EPILOG)
def detect() -> None:
    """Detection rule evaluation and efficacy analysis.

    \b
    Detection commands help you:
    • Evaluate rule efficacy using production metrics
    • Analyze signal quality and severity alignment
    • Generate recommendations for rule improvements
    • Score rules based on multiple dimensions
    • Review signal distribution across severity levels

    \b
    Requirements:
    • ClickHouse connection for metrics
    • Anthropic API key for semantic analysis
    • Rule evaluator configuration (see investigations/I-0012/)
    """


@detect.command()
@click.option("--top", default=20, type=int, help="Number of rules to evaluate (default: 20)")
@click.option("--deep-analysis", default=5, type=int, help="Number of rules for manual classification (default: 5)")
@click.option("--output", default="./results/", type=click.Path(), help="Output directory for results (default: ./results/)")
@click.option("--config", type=click.Path(exists=True), help="Path to rule evaluator config YAML")
@click.option("--skip-semantic", is_flag=True, help="Skip LLM semantic analysis (faster, metrics only)")
def evaluate(top: int, deep_analysis: int, output: str, config: Optional[str], skip_semantic: bool) -> None:
    """Evaluate detection rules for efficacy and generate recommendations.

    \b
    Runs a comprehensive evaluation workflow:
    1. Query ClickHouse for rule metrics (fire count, severity, etc.)
    2. Calculate selectivity and severity scores
    3. Run semantic analysis via Anthropic API (optional)
    4. Generate recommendations for rule improvements
    5. Export results to JSON and Markdown reports

    \b
    The evaluation considers:
    • Fire count (how often the rule triggers)
    • Selectivity (signal-to-noise ratio)
    • Severity alignment (are critical signals actually critical?)
    • Semantic quality (rule description vs behavior)

    \b
    Output includes:
    • recommendations.json - Machine-readable recommendations
    • efficacy_report.md - Human-readable summary
    • rule_scores.csv - Detailed scoring breakdown

    \b
    Examples:
      # Standard evaluation (20 rules, 5 deep analysis)
      athf detect evaluate

      # Quick metrics-only evaluation
      athf detect evaluate --skip-semantic --top 10

      # Full evaluation with custom config
      athf detect evaluate --top 50 --config ./my-config.yaml

    \b
    Note:
      This command requires the rule_evaluator package from investigations/I-0012/
      and access to ClickHouse metrics database.
    """
    logger.info(f"Starting evaluation: top={top}, deep_analysis={deep_analysis}, skip_semantic={skip_semantic}")

    try:
        # Try to import rule_evaluator components
        # Add the scripts directory to path (same pattern as tests)
        sys.path.insert(0, str(Path("/Users/ebrown/nebulock/detect-vault/scripts")))
        from rule_evaluator.config import load_config
        from rule_evaluator import clickhouse_queries
        from rule_evaluator.scorer import (
            PrecisionProxyCalculator,
            VolumeManageabilityCalculator,
        )
        from rule_evaluator.sql_analyzer import SQLQualityAnalyzer
        from rule_evaluator.severity_evaluator import SeverityAlignmentEvaluator
        from rule_evaluator.selectivity_calculator import SelectivityCalculator
        from rule_evaluator.efficacy_scorer import EfficacyScorer
        from rule_evaluator.classifier import InteractiveClassifier
        from rule_evaluator.filter_generator import FilterPatternAggregator
        from rule_evaluator.recommender import RecommendationEngine
        from rule_evaluator.reports.detail_generator import (
            DetailReportGenerator,
            RuleEvaluationResult,
        )
        from im_evaluator.clickhouse_client import (
            MultiEnvClickHouseClient,
            EnvironmentConfig,
            ClickHouseConnectionError as CHConnectionError,
            ClickHouseQueryError,
        )
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
        logger.info("Successfully imported rule_evaluator components")
    except ImportError as e:
        logger.error(f"Failed to import rule_evaluator: {e}")
        console.print("\n[bold red]Error: Rule evaluator not found[/bold red]\n")
        console.print(f"Could not import rule_evaluator: {e}\n")
        console.print("Make sure you have:")
        console.print("  1. investigations/I-0012/scripts/rule_evaluator/ available")
        console.print("  2. Required dependencies installed (clickhouse-connect, anthropic)")
        console.print(f"  3. Python path includes information-model-schema\n")
        sys.exit(1)

    # Setup interrupt handler for graceful Ctrl+C
    setup_interrupt_handler()

    console.print("\n[bold cyan]🔍 Detection Rule Evaluator[/bold cyan]\n")

    # Validate inputs early
    try:
        # Validate configuration file
        config_path = Path(config) if config else None
        validate_config_file(config_path)

        # Validate output directory
        output_dir = validate_output_directory(output)

        # Validate parameters
        if top <= 0:
            raise ValidationError("--top must be greater than 0")
        if deep_analysis < 0:
            raise ValidationError("--deep-analysis must be >= 0")
        if deep_analysis > top:
            logger.warning(f"deep_analysis ({deep_analysis}) > top ({top}), adjusting to {top}")
            deep_analysis = top

        logger.info("Input validation successful")

    except (ConfigurationError, ValidationError) as e:
        logger.error(f"Validation failed: {e}")
        console.print(f"\n[bold red]Validation Error:[/bold red] {e}\n")
        sys.exit(1)

    # Display configuration
    config_table = Table(show_header=False, box=None)
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="white")
    config_table.add_row("Rules to evaluate", str(top))
    config_table.add_row("Deep analysis", str(deep_analysis))
    config_table.add_row("Output directory", str(output_dir))
    config_table.add_row("Semantic analysis", "Disabled" if skip_semantic else "Enabled")

    console.print(Panel(config_table, title="Evaluation Configuration", border_style="blue"))

    try:
        # Load configuration
        start_time = time.time()
        logger.info(f"Loading configuration from: {config_path or 'default'}")
        cfg = load_config(config_path)
        logger.info(f"Configuration loaded in {time.time() - start_time:.2f}s")

        console.print("\n[bold]Step 1: Connecting to ClickHouse...[/bold]")
        logger.info(f"Connecting to ClickHouse: {cfg.clickhouse.host}:{cfg.clickhouse.port}")

        # Build environment config from rule_evaluator config
        env_config = EnvironmentConfig(
            name="prod",
            host=cfg.clickhouse.host,
            port=cfg.clickhouse.port,
            username=cfg.clickhouse.user,
            password=cfg.clickhouse.password,
            database=cfg.clickhouse.database,
            secure=cfg.clickhouse.secure,
        )

        # Initialize multi-env client with retry logic
        @retry_on_transient_error(max_attempts=3, backoff_factor=2.0)
        def connect_and_test() -> MultiEnvClickHouseClient:
            client = MultiEnvClickHouseClient(
                environments=["prod"],
                configs={"prod": env_config},
            )
            # Test connection immediately
            if not client.get_env("prod").test_connection():
                raise ClickHouseConnectionError(
                    f"Failed to connect to ClickHouse at {cfg.clickhouse.host}:{cfg.clickhouse.port}\n"
                    f"Possible issues:\n"
                    f"  • Check host and port are correct\n"
                    f"  • Verify credentials in config file\n"
                    f"  • Ensure ClickHouse server is running\n"
                    f"  • Check network connectivity and firewall rules"
                )
            return client

        try:
            conn_start = time.time()
            client = connect_and_test()
            conn_time = time.time() - conn_start
            logger.info(f"ClickHouse connection established in {conn_time:.2f}s")
            console.print(f"[green]✓ Connected to ClickHouse ({conn_time:.2f}s)[/green]\n")
        except ClickHouseConnectionError as e:
            logger.error(f"ClickHouse connection failed: {e}")
            console.print(f"\n[bold red]✗ Connection Failed[/bold red]\n")
            console.print(str(e))
            sys.exit(1)

        # Step 2: Fetch top N rules by dropped findings
        console.print(f"[bold]Step 2: Fetching top {top} rules by dropped findings...[/bold]")
        logger.info(f"Querying top {top} rules (days_lookback={cfg.evaluation.days_lookback}, timeout={cfg.evaluation.query_timeout}s)")

        @retry_on_transient_error(max_attempts=3, backoff_factor=2.0)
        def fetch_rules() -> list:
            query_start = time.time()
            rules = clickhouse_queries.get_top_rules_by_dropped_findings(
                client=client,
                environment="prod",
                days=cfg.evaluation.days_lookback,
                min_severity=cfg.evaluation.min_severity,
                limit=top,
                timeout=cfg.evaluation.query_timeout,
            )
            query_time = time.time() - query_start
            logger.info(f"Rule query completed in {query_time:.2f}s, found {len(rules)} rules")
            return rules

        try:
            rule_stats = fetch_rules()
        except ClickHouseQueryError as e:
            logger.error(f"Query failed: {e}")
            console.print(f"\n[bold red]✗ Query Failed[/bold red]\n")
            console.print(f"Error: {e}\n")
            console.print("Suggestions:")
            console.print(f"  • Increase query timeout (current: {cfg.evaluation.query_timeout}s)")
            console.print(f"  • Reduce lookback period (current: {cfg.evaluation.days_lookback} days)")
            console.print("  • Check ClickHouse server load\n")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error fetching rules: {e}")
            console.print(f"\n[bold red]✗ Unexpected Error[/bold red]\n")
            console.print(f"Error: {e}\n")
            sys.exit(1)

        if not rule_stats:
            logger.warning("No rules found with dropped findings")
            console.print("[yellow]No rules found with dropped findings[/yellow]\n")
            console.print("This could mean:")
            console.print("  • No rules triggered in the lookback period")
            console.print("  • All findings were escalated (not dropped)")
            console.print(f"  • Check the min_severity filter (current: {cfg.evaluation.min_severity})\n")
            sys.exit(0)

        console.print(f"[green]✓ Found {len(rule_stats)} rules[/green]\n")

        # Step 3: Calculate scores for each rule
        console.print(f"[bold]Step 3: Calculating scores for {len(rule_stats)} rules...[/bold]\n")
        logger.info(f"Starting score calculation for {len(rule_stats)} rules")
        eval_start_time = time.time()

        evaluation_results = []
        failed_rules = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Evaluating rules...", total=len(rule_stats))

            for idx, stats in enumerate(rule_stats, 1):
                # Check for interrupt
                if _interrupted:
                    logger.warning(f"Interrupted during evaluation at rule {idx}/{len(rule_stats)}")
                    console.print(f"\n[yellow]Interrupted. Processed {len(evaluation_results)}/{len(rule_stats)} rules.[/yellow]")
                    break

                try:
                    logger.debug(f"Processing rule {idx}/{len(rule_stats)}: {stats.trigger_id}")
                    # Calculate precision proxy
                    precision_result = PrecisionProxyCalculator.calculate(
                        dropped_finding_count=stats.dropped_finding_count,
                        raw_signal_count=stats.raw_signal_count,
                    )

                    # Calculate volume manageability
                    volume_result = VolumeManageabilityCalculator.calculate(
                        raw_signal_count=stats.raw_signal_count,
                        days=cfg.evaluation.days_lookback,
                    )

                    # Get rule metadata for SQL and severity analysis
                    rule_metadata_list = clickhouse_queries.get_rule_metadata(
                        client=client,
                        environment="prod",
                        trigger_ids=[stats.trigger_id],
                        timeout=cfg.evaluation.query_timeout,
                    )

                    if not rule_metadata_list:
                        logger.warning(f"No metadata found for rule {stats.trigger_id}, skipping")
                        failed_rules.append((stats.trigger_id, "No metadata available"))
                        progress.advance(task)
                        continue

                    rule_metadata = rule_metadata_list[0]

                    # Calculate SQL quality score
                    sql_score = 50.0  # Default if no SQL available
                    if rule_metadata.query_sql:
                        sql_result = SQLQualityAnalyzer.analyze(rule_metadata.query_sql)
                        sql_score = sql_result.score

                    # Calculate severity alignment (skip if --skip-semantic)
                    severity_score = 50.0  # Default/neutral score
                    if not skip_semantic and rule_metadata.description:
                        try:
                            severity_evaluator = SeverityAlignmentEvaluator(
                                anthropic_api_key=cfg.anthropic.api_key,
                                model=cfg.anthropic.model,
                            )
                            severity_result = severity_evaluator.evaluate(
                                description=rule_metadata.description,
                                actual_severity=rule_metadata.severity,
                            )
                            severity_score = severity_result.alignment_score
                            logger.debug(f"Severity score for {stats.trigger_id}: {severity_score}")
                        except Exception as e:
                            logger.warning(f"Severity evaluation failed for {stats.trigger_id}: {e}")
                            console.print(f"[yellow]Warning: Severity evaluation failed for {stats.trigger_id}: {str(e)[:80]}[/yellow]")

                    # Calculate selectivity (optional)
                    selectivity_score = None
                    if rule_metadata.query_sql:
                        try:
                            selectivity_calc = SelectivityCalculator(client=client, environment="prod")
                            selectivity_metrics = selectivity_calc.calculate(
                                query_sql=rule_metadata.query_sql,
                                days=cfg.evaluation.days_lookback,
                                timeout=cfg.evaluation.query_timeout,
                            )
                            if selectivity_metrics:
                                selectivity_score = selectivity_metrics.score
                                logger.debug(f"Selectivity score for {stats.trigger_id}: {selectivity_score}")
                        except Exception as e:
                            logger.debug(f"Selectivity calculation failed for {stats.trigger_id}: {e}")
                            # Selectivity is optional, so we continue

                    # Calculate overall efficacy score
                    efficacy_result = EfficacyScorer.calculate(
                        trigger_id=stats.trigger_id,
                        precision_score=precision_result.score,
                        volume_score=volume_result.score,
                        severity_score=severity_score,
                        sql_score=sql_score,
                        selectivity_score=selectivity_score,
                    )

                    # Generate recommendations
                    recommendations = RecommendationEngine.generate(
                        trigger_id=stats.trigger_id,
                        efficacy_score=efficacy_result.score,
                        precision_score=precision_result.score,
                        volume_score=volume_result.score,
                        severity_score=severity_score,
                        sql_score=sql_score,
                        selectivity_score=selectivity_score,
                        filter_recommendations=None,  # Will be added during deep analysis
                    )

                    # Store result
                    eval_result = RuleEvaluationResult(
                        trigger_id=stats.trigger_id,
                        rule_name=rule_metadata.name,
                        rule_metadata=rule_metadata,
                        efficacy_result=efficacy_result,
                        recommendations=recommendations,
                        metrics={
                            "precision_score": precision_result.score,
                            "volume_score": volume_result.score,
                            "severity_score": severity_score,
                            "sql_score": sql_score,
                            "selectivity_score": selectivity_score,
                            "dropped_finding_count": stats.dropped_finding_count,
                            "raw_signal_count": stats.raw_signal_count,
                        },
                    )
                    evaluation_results.append(eval_result)
                    logger.debug(f"Successfully evaluated rule {stats.trigger_id} (efficacy: {efficacy_result.score:.1f})")

                except Exception as e:
                    logger.error(f"Failed to evaluate rule {stats.trigger_id}: {e}", exc_info=True)
                    failed_rules.append((stats.trigger_id, str(e)[:100]))
                    console.print(f"[yellow]⚠ Failed to evaluate {stats.trigger_id}: {str(e)[:80]}[/yellow]")

                progress.advance(task)

        eval_time = time.time() - eval_start_time
        logger.info(f"Score calculation completed in {eval_time:.2f}s: {len(evaluation_results)} successful, {len(failed_rules)} failed")

        if failed_rules:
            console.print(f"\n[yellow]⚠ {len(failed_rules)} rule(s) failed to evaluate[/yellow]")
            logger.warning(f"Failed rules: {[rule_id for rule_id, _ in failed_rules]}")

        console.print(f"[green]✓ Calculated scores for {len(evaluation_results)} rules[/green]\n")

        # Step 4: Run interactive classifier on worst rules (deep analysis)
        if deep_analysis > 0 and evaluation_results:
            console.print(f"[bold]Step 4: Running deep analysis on worst {deep_analysis} rules...[/bold]\n")

            # Sort by efficacy score (worst first) and take top N
            worst_rules = sorted(evaluation_results, key=lambda r: r.efficacy_result.score)[:deep_analysis]

            for eval_result in worst_rules:
                console.print(f"[cyan]Analyzing: {eval_result.rule_name}[/cyan]")

                # Fetch sample signals for classification
                sample_signals = clickhouse_queries.get_sample_signals(
                    client=client,
                    environment="prod",
                    trigger_id=eval_result.trigger_id,
                    days=cfg.evaluation.days_lookback,
                    limit=10,
                    timeout=cfg.evaluation.query_timeout,
                )

                if not sample_signals:
                    console.print("[yellow]No signals found for classification[/yellow]\n")
                    continue

                # Fetch events for signals
                all_event_ids = []
                for signal in sample_signals:
                    all_event_ids.extend(signal.event_ids)

                events = []
                if all_event_ids:
                    events = clickhouse_queries.get_events_by_ids(
                        client=client,
                        environment="prod",
                        event_ids=all_event_ids[:100],  # Limit to prevent timeout
                        days=cfg.evaluation.days_lookback,
                        timeout=cfg.evaluation.query_timeout,
                    )

                # Build events_by_signal mapping
                events_by_signal: dict[str, list[Any]] = {}
                for signal in sample_signals:
                    signal_events = [e for e in events if e.event_id in signal.event_ids]
                    events_by_signal[signal.signal_id] = signal_events

                # Run interactive classifier
                output_dir = Path(output)
                output_dir.mkdir(parents=True, exist_ok=True)
                classifier_output = output_dir / f"classifications_{eval_result.trigger_id}.json"

                classifier = InteractiveClassifier(
                    output_path=classifier_output,
                    analyst_name=None,
                )

                classifications = classifier.classify_signals(
                    signals=sample_signals,
                    events_by_signal=events_by_signal,
                )

                # Store classifications in eval result
                eval_result.classifications = classifications

                # Generate filter recommendations from classifications
                if classifications:
                    aggregator = FilterPatternAggregator()
                    filter_recs_dict = aggregator.aggregate(classifications)

                    # Get filter recommendations for this rule
                    filter_recs = filter_recs_dict.get(eval_result.trigger_id)

                    # Regenerate recommendations with filter patterns
                    eval_result.recommendations = RecommendationEngine.generate(
                        trigger_id=eval_result.trigger_id,
                        efficacy_score=eval_result.efficacy_result.score,
                        precision_score=eval_result.metrics["precision_score"],
                        volume_score=eval_result.metrics["volume_score"],
                        severity_score=eval_result.metrics["severity_score"],
                        sql_score=eval_result.metrics["sql_score"],
                        selectivity_score=eval_result.metrics.get("selectivity_score"),
                        filter_recommendations=filter_recs,
                    )

                console.print("[green]✓ Classification complete[/green]\n")
        else:
            console.print("[bold]Step 4: Skipping deep analysis (deep-analysis=0)[/bold]\n")

        # Step 5: Generate reports
        if not evaluation_results:
            logger.warning("No evaluation results to report")
            console.print("\n[yellow]⚠ No evaluation results to generate reports from[/yellow]\n")
            if _interrupted:
                console.print("[yellow]Operation was interrupted before any rules could be evaluated[/yellow]\n")
            sys.exit(0)

        console.print(f"[bold]Step 5: Generating reports...[/bold]")
        logger.info(f"Generating reports for {len(evaluation_results)} rules")
        report_start = time.time()

        output_dir = Path(output)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write recommendations JSON
        try:
            recommendations_file = output_dir / "recommendations.json"
            logger.debug(f"Writing recommendations to {recommendations_file}")
            with recommendations_file.open("w") as f:
                recommendations_data = [
                    {
                        "trigger_id": r.trigger_id,
                        "rule_name": r.rule_name,
                        "efficacy_score": r.efficacy_result.score,
                        "efficacy_tier": r.efficacy_result.tier.value,
                        "recommendations": r.recommendations.to_dict(),
                        "metrics": r.metrics,
                    }
                    for r in evaluation_results
                ]
                json.dump(recommendations_data, f, indent=2)
            logger.info(f"Wrote recommendations JSON: {recommendations_file}")
            console.print(f"[green]✓ Wrote {recommendations_file}[/green]")
        except Exception as e:
            logger.error(f"Failed to write recommendations JSON: {e}")
            console.print(f"[red]✗ Failed to write recommendations.json: {e}[/red]")

        # Write detailed report
        try:
            detail_generator = DetailReportGenerator()
            detail_report_file = output_dir / "detailed_evaluation.md"
            logger.debug(f"Writing detailed report to {detail_report_file}")
            detail_generator.generate(
                results=evaluation_results,
                output_path=detail_report_file,
            )
            logger.info(f"Wrote detailed report: {detail_report_file}")
            console.print(f"[green]✓ Wrote {detail_report_file}[/green]")
        except Exception as e:
            logger.error(f"Failed to write detailed report: {e}")
            console.print(f"[red]✗ Failed to write detailed_evaluation.md: {e}[/red]")

        # Write rule scores CSV
        try:
            scores_file = output_dir / "rule_scores.csv"
            logger.debug(f"Writing rule scores to {scores_file}")
            with scores_file.open("w") as f:
                # Header
                f.write("trigger_id,rule_name,efficacy_score,efficacy_tier,precision_score,volume_score,severity_score,sql_score,selectivity_score,dropped_findings,raw_signals\n")
                # Rows
                for r in evaluation_results:
                    f.write(
                        f"{r.trigger_id},"
                        f"{r.rule_name},"
                        f"{r.efficacy_result.score:.2f},"
                        f"{r.efficacy_result.tier.value},"
                        f"{r.metrics['precision_score']:.2f},"
                        f"{r.metrics['volume_score']:.2f},"
                        f"{r.metrics['severity_score']:.2f},"
                        f"{r.metrics['sql_score']:.2f},"
                        f"{r.metrics.get('selectivity_score', 0.0):.2f},"
                        f"{r.metrics['dropped_finding_count']},"
                        f"{r.metrics['raw_signal_count']}\n"
                    )
            logger.info(f"Wrote rule scores CSV: {scores_file}")
            console.print(f"[green]✓ Wrote {scores_file}[/green]")
        except Exception as e:
            logger.error(f"Failed to write rule scores CSV: {e}")
            console.print(f"[red]✗ Failed to write rule_scores.csv: {e}[/red]")

        report_time = time.time() - report_start
        logger.info(f"Report generation completed in {report_time:.2f}s")
        console.print()

        # Step 6: Display summary
        console.print("[bold]Step 6: Evaluation Summary[/bold]\n")

        # Calculate tier distribution
        tier_counts: dict[str, int] = {}
        for result in evaluation_results:
            tier = result.efficacy_result.tier.value
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        # Create summary table
        summary_table = Table(title="Rule Efficacy Distribution")
        summary_table.add_column("Tier", style="cyan")
        summary_table.add_column("Count", justify="right", style="yellow")
        summary_table.add_column("Percentage", justify="right", style="green")

        for tier in ["critical", "medium", "low", "monitor"]:
            count = tier_counts.get(tier, 0)
            pct = (count / len(evaluation_results)) * 100 if evaluation_results else 0
            summary_table.add_row(tier.capitalize(), str(count), f"{pct:.1f}%")

        console.print(summary_table)
        console.print()

        # Top 5 worst rules
        worst_5 = sorted(evaluation_results, key=lambda r: r.efficacy_result.score)[:5]
        worst_table = Table(title="Top 5 Rules Requiring Attention")
        worst_table.add_column("Rank", justify="right", style="cyan")
        worst_table.add_column("Rule Name", style="white")
        worst_table.add_column("Efficacy", justify="right", style="red")
        worst_table.add_column("Priority", style="yellow")

        for i, result in enumerate(worst_5, 1):
            worst_table.add_row(
                str(i),
                result.rule_name[:50],
                f"{result.efficacy_result.score:.1f}",
                result.recommendations.priority.value,
            )

        console.print(worst_table)
        console.print()

        console.print(Panel(
            f"[green]✓ Evaluation complete![/green]\n\n"
            f"Results written to: [cyan]{output}[/cyan]\n"
            f"- recommendations.json\n"
            f"- detailed_evaluation.md\n"
            f"- rule_scores.csv",
            title="Success",
            border_style="green",
        ))

    except KeyboardInterrupt:
        logger.warning("Evaluation interrupted by user")
        console.print("\n[yellow]⚠ Evaluation interrupted by user[/yellow]")
        if evaluation_results:
            console.print(f"[cyan]Partial results saved for {len(evaluation_results)} rules[/cyan]")
        sys.exit(130)  # Standard exit code for SIGINT
    except (ConfigurationError, ValidationError, ClickHouseConnectionError) as e:
        # Expected errors with user-friendly messages already displayed
        logger.error(f"Expected error during evaluation: {type(e).__name__}: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during evaluation: {e}", exc_info=True)
        console.print(f"\n[bold red]Unexpected Error:[/bold red] {e}")
        console.print("\nPlease check:")
        console.print("  • Log file: ~/.athf/logs/detect.log")
        console.print("  • Configuration file settings")
        console.print("  • ClickHouse connectivity")
        console.print("\nIf the problem persists, please report this issue.\n")
        sys.exit(1)


@detect.command()
@click.option("--rule-name", required=True, help="Name of the rule to score")
@click.option("--config", type=click.Path(exists=True), help="Path to rule evaluator config YAML")
def score(rule_name: str, config: Optional[str]) -> None:
    """Score a specific detection rule.

    \b
    Calculates comprehensive scoring for a single rule:
    • Precision proxy (from drop rate)
    • Volume manageability (from signal volume)
    • SQL quality (from query structure)
    • Query selectivity (from input/output ratio)
    • Overall efficacy (weighted combination)

    \b
    Examples:
      # Score a specific rule
      athf detect score --rule-name okta_anomalous_authentication

      # Score with custom config
      athf detect score --rule-name aws_s3_bucket_public --config ./my-config.yaml

    \b
    Output:
      Displays a detailed scoring breakdown in a Rich table with metrics,
      scores, interpretation tiers, and metric weights.
    """
    logger.info(f"Starting score command for rule: {rule_name}")

    # Validate rule name format
    if not rule_name or len(rule_name.strip()) == 0:
        logger.error("Empty rule name provided")
        console.print("[bold red]Error:[/bold red] Rule name cannot be empty")
        sys.exit(1)

    try:
        sys.path.insert(0, str(Path("/Users/ebrown/nebulock/detect-vault/scripts")))
        from rule_evaluator.config import load_config
        from investigations.I_0012.scripts.rule_evaluator.clickhouse_queries import (
            get_rule_metadata,
            get_top_rules_by_dropped_findings,
            test_connection,
        )
        from investigations.I_0012.scripts.rule_evaluator.scorer import (
            PrecisionProxyCalculator,
            VolumeManageabilityCalculator,
        )
        from investigations.I_0012.scripts.rule_evaluator.sql_analyzer import SQLQualityAnalyzer
        from investigations.I_0012.scripts.rule_evaluator.selectivity_calculator import (
            QuerySelectivityCalculator,
        )
        from investigations.I_0012.scripts.rule_evaluator.efficacy_scorer import EfficacyScorer
        from im_evaluator.clickhouse_client import MultiEnvClickHouseClient
        logger.info("Successfully imported rule_evaluator components")
    except ImportError as e:
        logger.error(f"Failed to import rule_evaluator: {e}")
        console.print(f"[bold red]Error:[/bold red] Could not import rule_evaluator: {e}")
        console.print("\nMake sure you have:")
        console.print("  1. investigations/I-0012/scripts/rule_evaluator/ available")
        console.print("  2. Required dependencies installed\n")
        sys.exit(1)

    try:
        # Validate and load configuration
        config_path = Path(config) if config else None
        try:
            validate_config_file(config_path)
            logger.info(f"Loading configuration from: {config_path or 'default'}")
            cfg = load_config(config_path)
            logger.info("Configuration loaded successfully")
        except ConfigurationError as e:
            logger.error(f"Configuration validation failed: {e}")
            console.print(f"\n[bold red]Configuration Error:[/bold red] {e}\n")
            sys.exit(1)

        console.print("[cyan]Connecting to ClickHouse...[/cyan]")
        logger.info(f"Connecting to ClickHouse: {cfg.clickhouse.host}:{cfg.clickhouse.port}")

        # Initialize ClickHouse client with retry logic
        @retry_on_transient_error(max_attempts=3, backoff_factor=2.0)
        def initialize_client() -> tuple[MultiEnvClickHouseClient, str]:
            ch_client = MultiEnvClickHouseClient(
                host=cfg.clickhouse.host,
                port=cfg.clickhouse.port,
                user=cfg.clickhouse.user,
                password=cfg.clickhouse.password,
                database=cfg.clickhouse.database,
                secure=cfg.clickhouse.secure,
            )

            # Test connection
            console.print("[cyan]Testing ClickHouse connection...[/cyan]")
            logger.debug("Testing ClickHouse connection")

            if not test_connection(ch_client, "prod"):
                logger.warning("Production connection failed, trying dev environment")
                console.print("[yellow]⚠ ClickHouse connection failed, trying dev environment[/yellow]")
                if not test_connection(ch_client, "dev"):
                    raise ClickHouseConnectionError(
                        "Could not connect to ClickHouse (tried both prod and dev)\n"
                        "Check:\n"
                        f"  • Host: {cfg.clickhouse.host}:{cfg.clickhouse.port}\n"
                        "  • Credentials in config file\n"
                        "  • Network connectivity and firewall"
                    )
                environment = "dev"
            else:
                environment = "prod"

            logger.info(f"Connected to ClickHouse environment: {environment}")
            return ch_client, environment

        try:
            ch_client, environment = initialize_client()
            console.print(f"[green]✓ Connected to ClickHouse ({environment})[/green]\n")
        except ClickHouseConnectionError as e:
            logger.error(f"ClickHouse connection failed: {e}")
            console.print(f"\n[bold red]Connection Failed:[/bold red]\n{e}\n")
            sys.exit(1)

        # Query all rules to find the one matching rule_name
        console.print("[cyan]Querying rules...[/cyan]")
        logger.info(f"Querying rules (days={cfg.evaluation.soak_period_days}, timeout={cfg.evaluation.query_timeout}s)")

        @retry_on_transient_error(max_attempts=3, backoff_factor=2.0)
        def query_rules() -> list:
            query_start = time.time()
            rules = get_top_rules_by_dropped_findings(
                ch_client,
                environment=environment,
                days=cfg.evaluation.soak_period_days,
                limit=1000,
                timeout=cfg.evaluation.query_timeout,
            )
            query_time = time.time() - query_start
            logger.info(f"Rule query completed in {query_time:.2f}s, found {len(rules)} rules")
            return rules

        try:
            all_rules = query_rules()
        except Exception as e:
            logger.error(f"Rule query failed: {e}")
            console.print(f"\n[bold red]Query Failed:[/bold red] {e}\n")
            console.print("Suggestions:")
            console.print(f"  • Increase query timeout (current: {cfg.evaluation.query_timeout}s)")
            console.print(f"  • Reduce lookback period (current: {cfg.evaluation.soak_period_days} days)")
            console.print("  • Check ClickHouse server status\n")
            sys.exit(1)

        if not all_rules:
            logger.error("No rules found in ClickHouse")
            console.print(f"[bold red]Error: No rules found in ClickHouse[/bold red]\n")
            console.print("Possible reasons:")
            console.print(f"  • No rules triggered in the last {cfg.evaluation.soak_period_days} days")
            console.print("  • Wrong database or environment")
            console.print("  • Check your data source\n")
            sys.exit(1)

        # Find matching rule by name (case-insensitive substring match)
        logger.info(f"Searching for rule matching: {rule_name}")
        matching_rule = None
        rule_name_lower = rule_name.lower()

        # Try substring match first (most flexible)
        for rule in all_rules:
            if rule_name_lower in rule.signal_title.lower() or rule_name_lower in rule.trigger_id.lower():
                matching_rule = rule
                logger.info(f"Found rule by substring match: {rule.trigger_id}")
                break

        # Try exact match on trigger_id if substring didn't work
        if not matching_rule:
            for rule in all_rules:
                if rule.trigger_id == rule_name:
                    matching_rule = rule
                    logger.info(f"Found rule by exact trigger_id match: {rule.trigger_id}")
                    break

        if not matching_rule:
            logger.error(f"Rule not found: {rule_name}")

            # Find similar rules for suggestions
            similar_rules = [
                r for r in all_rules
                if any(word in r.signal_title.lower() or word in r.trigger_id.lower()
                       for word in rule_name_lower.split('_'))
            ][:5]

            console.print(f"[bold red]Error: Rule '{rule_name}' not found[/bold red]\n")

            if similar_rules:
                console.print("Did you mean one of these?")
                for i, r in enumerate(similar_rules, 1):
                    console.print(f"  {i}. [cyan]{r.signal_title}[/cyan] ({r.trigger_id})")
            else:
                console.print("Available rules (first 10):")
                for i, r in enumerate(all_rules[:10], 1):
                    console.print(f"  {i}. [cyan]{r.signal_title}[/cyan] ({r.trigger_id})")

            console.print(f"\nTip: You can use partial names. Try 'athf detect score --rule-name <partial_name>'")
            raise RuleNotFoundError(f"Rule '{rule_name}' not found")

        console.print(f"[green]✓ Found rule: {matching_rule.signal_title}[/green]\n")
        logger.info(f"Successfully found rule: {matching_rule.trigger_id}")

        # Get detailed metadata
        console.print("[cyan]Fetching rule metadata...[/cyan]")
        metadata_dict = get_rule_metadata(
            ch_client,
            environment,
            [matching_rule.trigger_id],
            timeout=cfg.evaluation.query_timeout,
        )

        if not metadata_dict:
            console.print("[yellow]⚠ Could not fetch detailed metadata, using available stats[/yellow]\n")
            query_sql = None
            description = matching_rule.signal_title
        else:
            rule_metadata = metadata_dict.get(matching_rule.trigger_id)
            query_sql = rule_metadata.query_sql if rule_metadata else None
            description = rule_metadata.description if rule_metadata else matching_rule.signal_title

        # Calculate all metrics
        console.print("[cyan]Calculating metrics...[/cyan]")

        # 1. Precision Proxy
        precision_result = PrecisionProxyCalculator.calculate(
            matching_rule.dropped_finding_count,
            matching_rule.raw_signal_count,
        )
        precision_score = precision_result.score

        # 2. Volume Manageability
        volume_result = VolumeManageabilityCalculator.calculate(matching_rule.raw_signal_count)
        volume_score = volume_result.score

        # 3. SQL Quality
        sql_result = SQLQualityAnalyzer.analyze(query_sql)
        sql_score = sql_result.score

        # 4. Query Selectivity (optional - may be skipped)
        selectivity_score = None
        selectivity_result = None
        if query_sql:
            try:
                selectivity_result = QuerySelectivityCalculator.calculate(
                    ch_client,
                    environment,
                    matching_rule.trigger_id,
                    query_sql,
                    matching_rule.raw_signal_count,
                    days=cfg.evaluation.soak_period_days,
                    timeout=cfg.evaluation.query_timeout,
                )
                if selectivity_result.score is not None:
                    selectivity_score = selectivity_result.score
            except Exception as e:
                console.print(f"[yellow]⚠ Could not calculate selectivity: {e}[/yellow]")

        # 5. Severity alignment (placeholder - would require LLM)
        # For now, use a simple heuristic: neutral default score
        severity_score = 50.0

        # Calculate overall efficacy
        efficacy_result = EfficacyScorer.calculate(
            matching_rule.trigger_id,
            precision_score,
            volume_score,
            severity_score,
            sql_score,
            selectivity_score,
        )

        console.print("[green]✓ Calculations complete[/green]\n")

        # Build and display results table
        results_table = Table(title=f"Rule Scoring: {matching_rule.signal_title}", show_header=True)
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Score", style="yellow", justify="right")
        results_table.add_column("Tier", style="green")
        results_table.add_column("Weight", justify="right")

        # Define tier display helper
        def tier_to_display(tier_name: str) -> str:
            tier_map = {
                "excellent": "[green]Excellent[/green]",
                "good": "[green]Good[/green]",
                "fair": "[yellow]Fair[/yellow]",
                "poor": "[red]Poor[/red]",
                "skipped": "[dim]Skipped[/dim]",
            }
            return tier_map.get(tier_name, tier_name)

        # Add metric rows
        results_table.add_row(
            "Precision Proxy",
            f"{precision_score:.1f}",
            tier_to_display(precision_result.interpretation.value),
            f"{efficacy_result.weights_used.get('precision', 0) * 100:.0f}%",
        )
        results_table.add_row(
            "Volume Manageability",
            f"{volume_score:.1f}",
            tier_to_display(volume_result.interpretation.value),
            f"{efficacy_result.weights_used.get('volume', 0) * 100:.0f}%",
        )
        results_table.add_row(
            "SQL Quality",
            f"{sql_score:.1f}",
            tier_to_display(sql_result.interpretation.value),
            f"{efficacy_result.weights_used.get('sql', 0) * 100:.0f}%",
        )

        if selectivity_score is not None:
            results_table.add_row(
                "Query Selectivity",
                f"{selectivity_score:.1f}",
                tier_to_display(selectivity_result.interpretation.value),
                f"{efficacy_result.weights_used.get('selectivity', 0) * 100:.0f}%",
            )
        else:
            results_table.add_row(
                "Query Selectivity",
                "N/A",
                "[dim]Skipped[/dim]",
                "—",
            )

        # Add separator
        results_table.add_row("", "", "", "")

        # Add overall efficacy
        results_table.add_row(
            "[bold]Overall Efficacy[/bold]",
            f"[bold]{efficacy_result.score:.1f}[/bold]",
            f"[bold]{tier_to_display(efficacy_result.tier.value)}[/bold]",
            "[bold]100%[/bold]",
        )

        console.print(results_table)

        # Display additional context
        console.print("\n[bold]Rule Details:[/bold]")
        details_table = Table(show_header=False, box=None)
        details_table.add_column("Label", style="cyan")
        details_table.add_column("Value", style="white")
        details_table.add_row("Trigger ID", matching_rule.trigger_id)
        details_table.add_row("Raw Signals (7d)", str(matching_rule.raw_signal_count))
        details_table.add_row("Dropped Findings (7d)", str(matching_rule.dropped_finding_count))
        details_table.add_row("Drop Rate", f"{precision_result.formula_breakdown['drop_rate']:.2%}")

        if query_sql:
            suggestions = sql_result.suggestions[:2] if sql_result.suggestions else ["None"]
            details_table.add_row("SQL Quality Issues", ", ".join(suggestions))

        console.print(details_table)

        console.print(f"\n[bold green]✓ Scoring complete[/bold green]")
        logger.info(f"Scoring completed successfully for rule: {rule_name}")

    except KeyboardInterrupt:
        logger.warning("Scoring interrupted by user")
        console.print("\n[yellow]⚠ Scoring interrupted by user[/yellow]")
        sys.exit(130)
    except (ConfigurationError, ClickHouseConnectionError, RuleNotFoundError) as e:
        # Expected errors with user-friendly messages already displayed
        logger.error(f"Expected error during scoring: {type(e).__name__}: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during scoring: {e}", exc_info=True)
        console.print(f"\n[bold red]Unexpected Error:[/bold red] {e}")
        console.print("\nDebug information has been logged to: ~/.athf/logs/detect.log")
        console.print("\nPlease check:")
        console.print("  • Configuration file settings")
        console.print("  • ClickHouse connectivity")
        console.print("  • Rule name spelling\n")
        sys.exit(1)


@detect.command()
@click.option("--config", type=click.Path(exists=True), help="Path to rule evaluator config YAML")
@click.option("--output-format", type=click.Choice(["table", "json"]), default="table", help="Output format")
def review_signals(config: Optional[str], output_format: str) -> None:
    """Review signal distribution across severity levels.

    \b
    Analyzes signal distribution to identify:
    • Over-represented severity levels (too many critical?)
    • Under-represented severity levels (missing low?)
    • Severity inflation patterns
    • Signal volume trends

    \b
    Examples:
      # Display signal distribution table
      athf detect review-signals

      # Export to JSON
      athf detect review-signals --output-format json

    \b
    Use this to:
      • Validate severity assignments are balanced
      • Identify rules that need severity recalibration
      • Track signal quality improvements over time
    """
    logger.info(f"Starting review-signals command (output_format={output_format})")
    console.print("\n[bold cyan]📈 Signal Distribution Review[/bold cyan]\n")

    try:
        sys.path.insert(0, str(Path("/Users/ebrown/nebulock/detect-vault/scripts")))
        from rule_evaluator.config import load_config
        from investigations.I_0012.scripts.rule_evaluator.clickhouse_queries import ClickHouseClient
        logger.info("Successfully imported rule_evaluator components")
    except ImportError as e:
        logger.error(f"Failed to import rule_evaluator: {e}")
        console.print(f"[bold red]Error:[/bold red] Could not import rule_evaluator: {e}")
        console.print("\nMake sure rule_evaluator package is available\n")
        sys.exit(1)

    try:
        # Validate and load configuration
        config_path = Path(config) if config else None
        try:
            validate_config_file(config_path)
            logger.info(f"Loading configuration from: {config_path or 'default'}")
            cfg = load_config(config_path)
            logger.info("Configuration loaded successfully")
        except ConfigurationError as e:
            logger.error(f"Configuration validation failed: {e}")
            console.print(f"\n[bold red]Configuration Error:[/bold red] {e}\n")
            sys.exit(1)

        console.print("[bold]Step 1: Connecting to ClickHouse...[/bold]")
        logger.info(f"Connecting to ClickHouse: {cfg.clickhouse.host}:{cfg.clickhouse.port}")

        # Initialize ClickHouse client
        from im_evaluator.clickhouse_client import ClickHouseConnectionError as CHConnectionError
        from im_evaluator.clickhouse_client import ClickHouseQueryError
        from im_evaluator.clickhouse_client import EnvironmentConfig
        from im_evaluator.clickhouse_client import MultiEnvClickHouseClient

        # Build environment config from rule_evaluator config
        env_config = EnvironmentConfig(
            name="prod",
            host=cfg.clickhouse.host,
            port=cfg.clickhouse.port,
            username=cfg.clickhouse.user,
            password=cfg.clickhouse.password,
            database=cfg.clickhouse.database,
            secure=cfg.clickhouse.secure,
        )

        # Initialize multi-env client with retry logic
        @retry_on_transient_error(max_attempts=3, backoff_factor=2.0)
        def connect_client() -> MultiEnvClickHouseClient:
            client = MultiEnvClickHouseClient(
                environments=["prod"],
                configs={"prod": env_config},
            )

            # Test connection
            console.print("[bold]Step 2: Testing connection...[/bold]")
            if not client.get_env("prod").test_connection():
                raise ClickHouseConnectionError(
                    f"Failed to connect to ClickHouse at {cfg.clickhouse.host}:{cfg.clickhouse.port}\n"
                    "Check configuration and connectivity"
                )
            return client

        try:
            conn_start = time.time()
            client = connect_client()
            conn_time = time.time() - conn_start
            logger.info(f"ClickHouse connection established in {conn_time:.2f}s")
            console.print(f"[green]✓ Connected to ClickHouse ({conn_time:.2f}s)[/green]\n")
        except ClickHouseConnectionError as e:
            logger.error(f"ClickHouse connection failed: {e}")
            console.print(f"\n[bold red]✗ Connection Failed[/bold red]\n{e}\n")
            sys.exit(1)

        # Query signal distribution by severity
        console.print("[bold]Step 3: Querying signal distribution (30-day window)...[/bold]")
        logger.info(f"Executing signal distribution query (timeout={cfg.evaluation.query_timeout}s)")
        query_start = time.time()

        query = """
        SELECT
            'Informational' AS severity_label,
            10 AS severity_num,
            COUNT(*) AS signal_count,
            COUNT(DISTINCT trigger_id) AS unique_rules,
            AVG(signal_count) AS avg_signals_per_rule
        FROM signals
        WHERE created_at >= now64(3) - INTERVAL 30 DAY
            AND JSONExtractInt(payload_json, 'severity') = 10
        UNION ALL
        SELECT
            'Low' AS severity_label,
            20 AS severity_num,
            COUNT(*) AS signal_count,
            COUNT(DISTINCT trigger_id) AS unique_rules,
            AVG(signal_count) AS avg_signals_per_rule
        FROM signals
        WHERE created_at >= now64(3) - INTERVAL 30 DAY
            AND JSONExtractInt(payload_json, 'severity') = 20
        UNION ALL
        SELECT
            'Medium' AS severity_label,
            30 AS severity_num,
            COUNT(*) AS signal_count,
            COUNT(DISTINCT trigger_id) AS unique_rules,
            AVG(signal_count) AS avg_signals_per_rule
        FROM signals
        WHERE created_at >= now64(3) - INTERVAL 30 DAY
            AND JSONExtractInt(payload_json, 'severity') = 30
        UNION ALL
        SELECT
            'High' AS severity_label,
            40 AS severity_num,
            COUNT(*) AS signal_count,
            COUNT(DISTINCT trigger_id) AS unique_rules,
            AVG(signal_count) AS avg_signals_per_rule
        FROM signals
        WHERE created_at >= now64(3) - INTERVAL 30 DAY
            AND JSONExtractInt(payload_json, 'severity') = 40
        UNION ALL
        SELECT
            'Critical' AS severity_label,
            50 AS severity_num,
            COUNT(*) AS signal_count,
            COUNT(DISTINCT trigger_id) AS unique_rules,
            AVG(signal_count) AS avg_signals_per_rule
        FROM signals
        WHERE created_at >= now64(3) - INTERVAL 30 DAY
            AND JSONExtractInt(payload_json, 'severity') = 50
        ORDER BY severity_num DESC
        """

        try:
            result = client.query("prod", query, timeout=cfg.evaluation.query_timeout)
            query_time = time.time() - query_start
            logger.info(f"Signal distribution query completed in {query_time:.2f}s")
        except ClickHouseQueryError as e:
            query_time = time.time() - query_start
            logger.error(f"Query failed after {query_time:.2f}s: {e}")
            console.print(f"\n[bold red]✗ Query Failed[/bold red]\n")
            console.print(f"Error: {e}\n")
            console.print("Suggestions:")
            console.print("  • Reduce the time window (currently 30 days)")
            console.print(f"  • Increase query timeout (current: {cfg.evaluation.query_timeout}s)")
            console.print("  • Try during off-peak hours\n")
            sys.exit(1)
        except CHConnectionError as e:
            logger.error(f"Connection error during query: {e}")
            console.print(f"\n[bold red]✗ Connection Error[/bold red]\n")
            console.print(f"Error: {e}\n")
            console.print("The connection was lost during the query. Try again.\n")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error during query: {e}", exc_info=True)
            console.print(f"\n[bold red]✗ Unexpected Error[/bold red]\n")
            console.print(f"Error: {e}\n")
            sys.exit(1)

        rows = result.to_dicts()
        logger.info(f"Query returned {len(rows)} severity levels")

        if not rows:
            console.print("\n[yellow]ℹ No signals found in the 30-day window[/yellow]\n")
            console.print("Possible reasons:")
            console.print("  • All signals are still in current period")
            console.print("  • Check your ClickHouse database has signal data")
            console.print("  • Verify connection and table names\n")
            sys.exit(0)

        # Format output
        if output_format == "json":
            # Calculate summary statistics
            total_signals = sum(row["signal_count"] for row in rows)
            total_rules = sum(row["unique_rules"] for row in rows)
            most_common_severity = max(rows, key=lambda r: r["signal_count"])["severity_label"]

            # Build JSON output
            output_data = {
                "severity_distribution": [
                    {
                        "severity": row["severity_label"].lower(),
                        "signal_count": int(row["signal_count"]),
                        "unique_rules": int(row["unique_rules"]),
                        "avg_per_rule": round(float(row["avg_signals_per_rule"]), 2)
                        if row["avg_signals_per_rule"]
                        else 0.0,
                    }
                    for row in rows
                ],
                "summary": {
                    "total_signals": total_signals,
                    "total_rules": total_rules,
                    "most_common_severity": most_common_severity.lower(),
                },
            }

            console.print_json(data=output_data)

        else:  # table format (default)
            # Create table
            table = Table(title="Signal Distribution (Last 30 Days)")
            table.add_column("Severity", style="cyan", justify="left")
            table.add_column("Signal Count", style="yellow", justify="right")
            table.add_column("Unique Rules", style="green", justify="right")
            table.add_column("Avg Per Rule", style="magenta", justify="right")

            for row in rows:
                table.add_row(
                    row["severity_label"],
                    f"{int(row['signal_count']):,}",
                    f"{int(row['unique_rules']):,}",
                    f"{float(row['avg_signals_per_rule'] or 0):.1f}",
                )

            console.print()
            console.print(table)
            console.print()

            # Print summary statistics
            total_signals = sum(row["signal_count"] for row in rows)
            total_rules = sum(row["unique_rules"] for row in rows)
            most_common = max(rows, key=lambda r: r["signal_count"])

            summary_table = Table(show_header=False, box=None)
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Value", style="white")
            summary_table.add_row("Total Signals", f"{total_signals:,}")
            summary_table.add_row("Total Unique Rules", f"{total_rules:,}")
            summary_table.add_row("Most Common Severity", most_common["severity_label"])
            summary_table.add_row(
                "Query Duration",
                f"{result.elapsed_seconds:.2f}s",
            )

            console.print(Panel(summary_table, title="Summary", border_style="blue"))
            console.print()

        logger.info("Signal review completed successfully")

    except KeyboardInterrupt:
        logger.warning("Signal review interrupted by user")
        console.print("\n[yellow]⚠ Signal review interrupted by user[/yellow]")
        sys.exit(130)
    except (ConfigurationError, ClickHouseConnectionError) as e:
        # Expected errors with user-friendly messages already displayed
        logger.error(f"Expected error during signal review: {type(e).__name__}: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during signal review: {e}", exc_info=True)
        console.print(f"\n[bold red]Unexpected Error:[/bold red] {e}")
        console.print("\nDebug information has been logged to: ~/.athf/logs/detect.log\n")
        sys.exit(1)


@detect.command()
@click.option("--input", required=True, type=click.Path(exists=True), help="Input recommendations JSON file")
@click.option("--output", default="./rules/", type=click.Path(), help="Output directory for YAML files")
@click.option("--dry-run", is_flag=True, help="Preview changes without writing files")
def generate_yaml(input: str, output: str, dry_run: bool) -> None:
    """Generate detection rule YAML from evaluation recommendations.

    \b
    Takes recommendations from evaluation and generates:
    • Updated rule YAML files with improved configurations
    • Severity adjustments based on analysis
    • Filter improvements for better selectivity
    • Documentation of changes made

    \b
    Examples:
      # Generate YAML from evaluation results
      athf detect generate-yaml --input ./results/recommendations.json

      # Preview changes without writing
      athf detect generate-yaml --input ./results/recs.json --dry-run

      # Write to specific directory
      athf detect generate-yaml --input ./recs.json --output ./new-rules/

    \b
    Output:
      Creates/updates YAML files in the output directory with recommended changes.
    """
    logger.info(f"Starting generate-yaml command (input={input}, output={output}, dry_run={dry_run})")
    console.print("\n[bold cyan]📝 Generating Detection Rule YAML[/bold cyan]\n")

    try:
        sys.path.insert(0, str(Path("/Users/ebrown/nebulock/detect-vault/scripts")))
        from rule_evaluator.models import RuleMetadata
        from investigations.I_0012.scripts.rule_evaluator.yaml_generator import YAMLGenerator
        from investigations.I_0012.scripts.rule_evaluator.yaml_generator import ValidationError as YAMLValidationError
        logger.info("Successfully imported rule_evaluator components")
    except ImportError as e:
        logger.error(f"Failed to import rule_evaluator: {e}")
        console.print(f"[bold red]Error:[/bold red] Could not import rule_evaluator: {e}")
        console.print("\nMake sure rule_evaluator package is available\n")
        sys.exit(1)

    # Validate input file
    input_path = Path(input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input}")
        console.print(f"[bold red]Error:[/bold red] Input file not found: {input}")
        console.print(f"\nExpected path: {input_path.absolute()}\n")
        sys.exit(1)

    if not input_path.is_file():
        logger.error(f"Input path is not a file: {input}")
        console.print(f"[bold red]Error:[/bold red] Input path is not a file: {input}\n")
        sys.exit(1)

    # Validate output directory (if not dry run)
    if not dry_run:
        try:
            output_dir = validate_output_directory(output)
            logger.info(f"Output directory validated: {output_dir}")
        except ValidationError as e:
            logger.error(f"Output directory validation failed: {e}")
            console.print(f"\n[bold red]Validation Error:[/bold red] {e}\n")
            sys.exit(1)
    else:
        output_dir = Path(output)

    console.print(f"Input file: [cyan]{input}[/cyan]")
    console.print(f"Output directory: [cyan]{output}[/cyan]")
    console.print(f"Mode: [yellow]{'DRY RUN' if dry_run else 'WRITE'}[/yellow]\n")

    # Load and validate recommendations JSON
    logger.info(f"Loading recommendations from: {input_path}")
    try:
        with input_path.open() as f:
            recommendations_data = json.load(f)
        logger.info("Successfully loaded recommendations JSON")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        console.print(f"[bold red]Error:[/bold red] Invalid JSON format: {e}")
        console.print(f"\nThe file {input} is not valid JSON.")
        console.print("Check for:")
        console.print("  • Missing or extra commas")
        console.print("  • Unmatched brackets or braces")
        console.print("  • Invalid escape sequences\n")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to read input file: {e}")
        console.print(f"[bold red]Error:[/bold red] Failed to read input file: {e}\n")
        sys.exit(1)

    # Validate JSON structure
    if not isinstance(recommendations_data, (dict, list)):
        logger.error("Invalid recommendations format: expected dict or list")
        console.print("[bold red]Error:[/bold red] Invalid recommendations format")
        console.print("Expected a JSON object or array\n")
        sys.exit(1)

    # Extract rules to process (support both dict with "rules" key and direct list)
    if isinstance(recommendations_data, dict):
        rules = recommendations_data.get("rules", [])
    else:
        rules = recommendations_data

    if not rules:
        logger.warning("No rules found in recommendations")
        console.print("[yellow]⚠ No rules found in recommendations[/yellow]")
        console.print("\nExpected JSON structure:")
        console.print('  {"rules": [...]}  or  [...]')
        console.print("\nCheck your input file format.\n")
        sys.exit(0)

    logger.info(f"Found {len(rules)} total rules")

    # Filter to actionable rules (tune or improve)
    actionable_rules = [
        r for r in rules
        if r.get("action") in ("tune", "improve")
    ]

    if not actionable_rules:
        logger.warning("No actionable rules found")
        console.print("[yellow]⚠ No actionable rules (action: 'tune' or 'improve')[/yellow]")
        console.print("\nRules with actions 'tune' or 'improve' will be processed.")
        console.print(f"Found {len(rules)} total rules, but none are actionable.\n")
        sys.exit(0)

    logger.info(f"Found {len(actionable_rules)} actionable rules")
    console.print(f"[cyan]{len(actionable_rules)}[/cyan] actionable rule(s) found\n")

    try:
        # Find detect-vault root (try common locations)
        detect_vault_root = None
        for candidate in [
            Path("/Users/ebrown/nebulock/detect-vault"),
            Path.cwd() / "detect-vault",
            Path.cwd().parent / "detect-vault",
        ]:
            if candidate.exists() and (candidate / "detections").exists():
                detect_vault_root = candidate
                break

        if not detect_vault_root:
            console.print("[yellow]⚠ detect-vault not found (validation will be skipped)[/yellow]")
            console.print("   Searched: /Users/ebrown/nebulock/detect-vault, ./detect-vault, ../detect-vault\n")

        # Initialize YAML generator
        output_dir = Path(output)
        try:
            generator = YAMLGenerator(
                detect_vault_root=detect_vault_root or Path.cwd(),
                output_dir=output_dir,
            )
            logger.info(f"Initialized YAML generator (output_dir={output_dir})")
        except Exception as e:
            logger.error(f"Failed to initialize YAML generator: {e}")
            console.print(f"[bold red]Error:[/bold red] Failed to initialize YAML generator: {e}\n")
            sys.exit(1)

        # Track results
        generated_count = 0
        updated_count = 0
        skipped_count = 0
        skipped_rules = []
        results = []

        # Setup interrupt handler
        setup_interrupt_handler()

        # Process rules
        logger.info(f"Starting YAML generation for {len(actionable_rules)} rules")
        gen_start = time.time()

        with Progress() as progress:
            task = progress.add_task(
                "[cyan]Generating YAMLs...",
                total=len(actionable_rules)
            )

            for idx, rule in enumerate(actionable_rules, 1):
                # Check for interrupt
                if _interrupted:
                    logger.warning(f"Interrupted during YAML generation at rule {idx}/{len(actionable_rules)}")
                    console.print(f"\n[yellow]Interrupted. Processed {generated_count + updated_count}/{len(actionable_rules)} rules.[/yellow]")
                    break

                trigger_id = rule.get("trigger_id", "unknown")
                rule_name = rule.get("name", trigger_id)
                action = rule.get("action", "unknown")

                logger.debug(f"Processing rule {idx}/{len(actionable_rules)}: {trigger_id}")

                try:
                    # Build rule metadata from recommendation
                    metadata = RuleMetadata(
                        trigger_id=trigger_id,
                        name=rule_name,
                        description=rule.get("description", ""),
                        severity=rule.get("current_severity_score", 50),
                        query_sql=rule.get("current_sql", ""),
                        mitre_tactics=rule.get("mitre_tactics", []),
                        mitre_techniques=rule.get("mitre_techniques", []),
                    )

                    # Build recommendations object (simplified)
                    from investigations.I_0012.scripts.rule_evaluator.recommender import (
                        RuleRecommendations,
                        RecommendationPriority,
                    )

                    # Map action to recommendations
                    priority = _map_priority(rule.get("priority", "medium"))
                    recommendations = RuleRecommendations(
                        trigger_id=trigger_id,
                        priority=priority,
                        efficacy_score=rule.get("efficacy_score", 50.0),
                        expected_efficacy_improvement=rule.get("expected_improvement", 0.0),
                        metrics=rule.get("metrics", {}),
                        filter_patterns=rule.get("filter_improvements"),
                    )

                    # Use improved SQL if available, otherwise current SQL
                    tuned_sql = rule.get("tuned_sql") or rule.get("current_sql", "")

                    if not dry_run:
                        # Generate or update YAML
                        try:
                            yaml_path = generator.generate(
                                trigger_id=trigger_id,
                                rule_metadata=metadata,
                                recommendations=recommendations,
                                tuned_sql=tuned_sql,
                            )

                            # Determine if created or updated
                            is_update = generator._find_existing_yaml(trigger_id) is not None
                            if is_update:
                                updated_count += 1
                                status = "Updated"
                            else:
                                generated_count += 1
                                status = "Generated"

                            results.append({
                                "rule": rule_name,
                                "action": action,
                                "status": status,
                                "changes": _build_changes_summary(rule),
                            })

                        except YAMLValidationError as e:
                            logger.warning(f"YAML validation failed for {trigger_id}: {e}")
                            skipped_count += 1
                            skipped_rules.append({
                                "rule": rule_name,
                                "reason": f"Validation failed: {str(e)[:100]}",
                            })
                            results.append({
                                "rule": rule_name,
                                "action": action,
                                "status": "Skipped",
                                "changes": "Validation failed",
                            })
                    else:
                        # Dry run: just collect what would be done
                        generated_count += 1
                        results.append({
                            "rule": rule_name,
                            "action": action,
                            "status": "Would Generate",
                            "changes": _build_changes_summary(rule),
                        })
                        logger.debug(f"Dry run: would generate YAML for {trigger_id}")

                except KeyError as e:
                    logger.error(f"Missing required field for {trigger_id}: {e}")
                    skipped_count += 1
                    skipped_rules.append({
                        "rule": rule_name,
                        "reason": f"Missing required field: {e}",
                    })
                    results.append({
                        "rule": rule_name,
                        "action": action,
                        "status": "Skipped",
                        "changes": f"Missing field: {e}",
                    })
                except Exception as e:
                    logger.error(f"Failed to generate YAML for {trigger_id}: {e}", exc_info=True)
                    skipped_count += 1
                    skipped_rules.append({
                        "rule": rule_name,
                        "reason": str(e)[:100],
                    })
                    results.append({
                        "rule": rule_name,
                        "action": action,
                        "status": "Skipped",
                        "changes": f"Error: {str(e)[:50]}",
                    })

                progress.update(task, advance=1)

        gen_time = time.time() - gen_start
        logger.info(f"YAML generation completed in {gen_time:.2f}s: {generated_count} generated, {updated_count} updated, {skipped_count} skipped")

        # Display results
        console.print("\n")
        if results:
            table = Table(title="Generation Results")
            table.add_column("Rule", style="cyan", max_width=35)
            table.add_column("Action", style="yellow")
            table.add_column("Status", style="green")
            table.add_column("Changes", max_width=40)

            for result in results:
                status_style = {
                    "Generated": "green",
                    "Updated": "cyan",
                    "Skipped": "red",
                    "Would Generate": "yellow",
                }.get(result["status"], "white")

                table.add_row(
                    result["rule"][:35],
                    result["action"],
                    f"[{status_style}]{result['status']}[/{status_style}]",
                    result["changes"],
                )

            console.print(table)

        # Display summary
        console.print()
        summary_table = Table(show_header=False, box=None)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", style="white")

        if not dry_run:
            summary_table.add_row("Generated", str(generated_count))
            summary_table.add_row("Updated", str(updated_count))
            summary_table.add_row("Skipped", str(skipped_count))
            summary_table.add_row("Output Directory", str(output_dir / "yaml-sidecars"))
        else:
            summary_table.add_row("Would Generate", str(generated_count))
            summary_table.add_row("Skipped", str(skipped_count))

        console.print(Panel(summary_table, title="Summary", border_style="blue"))

        # Show skipped rules details if any
        if skipped_rules:
            console.print("\n[yellow]Skipped Rules:[/yellow]")
            for skipped in skipped_rules:
                console.print(f"  • [cyan]{skipped['rule']}[/cyan]: {skipped['reason']}")

            if dry_run:
                console.print("\n[yellow]Dry run mode - no files were written[/yellow]")

            logger.info("YAML generation command completed successfully")

    except KeyboardInterrupt:
        logger.warning("YAML generation interrupted by user")
        console.print("\n[yellow]⚠ YAML generation interrupted by user[/yellow]")
        if generated_count + updated_count > 0:
            console.print(f"[cyan]Partial results: {generated_count + updated_count} rules processed[/cyan]")
        sys.exit(130)
    except (ValidationError, YAMLValidationError) as e:
        # Validation errors already logged and displayed
        logger.error(f"Validation error during YAML generation: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during YAML generation: {e}", exc_info=True)
        console.print(f"\n[bold red]Unexpected Error:[/bold red] {e}")
        console.print("\nDebug information has been logged to: ~/.athf/logs/detect.log")
        console.print("\nPlease check:")
        console.print("  • Input JSON file format")
        console.print("  • Output directory permissions")
        console.print("  • Rule data completeness\n")
        sys.exit(1)


def _map_priority(priority_str: str) -> Any:
    """Map priority string to RecommendationPriority enum."""
    try:
        from investigations.I_0012.scripts.rule_evaluator.recommender import RecommendationPriority
        priority_map = {
            "critical": RecommendationPriority.CRITICAL,
            "medium": RecommendationPriority.MEDIUM,
            "low": RecommendationPriority.LOW,
            "monitor": RecommendationPriority.MONITOR,
        }
        return priority_map.get(priority_str.lower(), RecommendationPriority.MEDIUM)
    except Exception:
        return "medium"


def _build_changes_summary(rule: dict[str, Any]) -> str:
    """Build a summary of changes for a rule."""
    changes = []

    if rule.get("recommended_severity") and rule.get("current_severity"):
        changes.append(f"Severity: {rule['current_severity']} → {rule['recommended_severity']}")

    if rule.get("filter_improvements"):
        count = len(rule["filter_improvements"]) if isinstance(rule["filter_improvements"], list) else 1
        changes.append(f"Filters: +{count} new")

    if rule.get("tuned_sql") and rule.get("current_sql") != rule.get("tuned_sql"):
        changes.append("SQL: updated")

    return ", ".join(changes) if changes else "No specific changes"


if __name__ == "__main__":
    detect()
