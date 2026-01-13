"""ATHF command-line interface."""

import random

import click
from rich.console import Console

from athf.__version__ import __version__
from athf.commands import context, env, hunt, init, investigate, research, similar
from athf.commands.agent import agent

console = Console()


EPILOG = """
\b
Examples:
  # Initialize a new hunting workspace
  athf init

  # Create your first hunt
  athf hunt new

  # Search for credential dumping hunts
  athf hunt search "credential dumping"

  # List all completed hunts
  athf hunt list --status completed

  # Show program statistics
  athf hunt stats

\b
Getting Started:
  1. Run 'athf init' to set up your workspace
  2. Run 'athf hunt new' to create your first hunt
  3. Document using the LOCK pattern (Learn → Observe → Check → Keep)
  4. Track findings and iterate

\b
Documentation:
  • Full docs: https://github.com/Nebulock-Inc/agentic-threat-hunting-framework
  • CLI reference: docs/CLI_REFERENCE.md
  • AI workflows: Run 'athf init' to get prompts/ai-workflow.md

\b
Need help? Run 'athf COMMAND --help' for command-specific help.

\b
Created by Sydney Marrone © 2025
"""


@click.group(epilog=EPILOG)
@click.version_option(
    version=__version__,
    prog_name="athf",
    message="%(prog)s version %(version)s\nAgentic Threat Hunting Framework\nCreated by Sydney Marrone © 2025",
)
def cli() -> None:
    """Agentic Threat Hunting Framework (ATHF) - Hunt management CLI

    \b
    ATHF gives your threat hunting program memory and agency by:
    • Structured documentation with the LOCK pattern
    • Hunt tracking and metrics across your program
    • AI-assisted hypothesis generation and workflows
    • MITRE ATT&CK coverage analysis

    \b
    Quick Start:
      athf init           Set up a new hunting workspace
      athf hunt new       Create a hunt from template
      athf hunt list      View all hunts
      athf hunt search    Find hunts by keyword
      athf hunt stats     Show program metrics
    """


# Register command groups
cli.add_command(init.init)
cli.add_command(hunt.hunt)
cli.add_command(investigate.investigate)
cli.add_command(research.research)

# Phase 1 commands (env, context, similar)
cli.add_command(env.env)
cli.add_command(context.context)
cli.add_command(similar.similar)

# Agent commands
cli.add_command(agent)


@cli.command(hidden=True)
def wisdom() -> None:
    """Security wisdom for threat hunters."""
    quotes = [
        "The best threat hunters build memory, not just alerts.",
        "Adversaries don't repeat signatures. They repeat behaviors.",
        "A hunt without findings is still a hunt. Absence of evidence is evidence.",
        "Your SIEM doesn't have a storage problem. It has a memory problem.",
        "Indicators expire. Behaviors persist.",
        "The top of the Pyramid of Pain is the adversary's comfort zone. Make them uncomfortable.",
        "Hunt for TTPs, not IOCs. Adversaries swap infrastructure daily, not tactics.",
        "False positives teach you about your environment. True positives teach you about adversaries.",
        "Every expert threat hunter started with their first hypothesis. Keep building.",
        "The LOCK pattern isn't just documentation—it's institutional memory.",
        "Threat intelligence tells you what to hunt. Your environment tells you how.",
        "Behavioral detections age like wine. Signature detections age like milk.",
        "The most dangerous threats blend in. Hunt for the subtle, not the obvious.",
        "A mature hunt program isn't measured by detections. It's measured by learning velocity.",
        "Pivoting is an art. Knowing when to stop pivoting is wisdom.",
        "Your baseline is your best threat intelligence. Protect it.",
        "Hunt like an adversary thinks: what would I do if I were already inside?",
        "The best detection is a hunt hypothesis validated repeatedly.",
        "Memory is the multiplier. Agency is the force.",
        "Document the hunt that found nothing—it eliminates hypotheses for everyone who comes after you.",
    ]

    console.print(f"\n💭 [italic]{random.choice(quotes)}[/italic]\n")


@cli.command(hidden=True)
def thrunt() -> None:
    """The real command all along."""
    console.print("\n[bold cyan]🎯 THRUNT MODE ACTIVATED[/bold cyan]\n")
    console.print("[italic]You've discovered the secret: threat hunting has always been 'thrunting'.[/italic]")
    console.print("[italic]Welcome to the club. Now go hunt some threats.[/italic]\n")


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
