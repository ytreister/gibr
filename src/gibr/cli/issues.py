"""CLI command to list open issues from the tracker."""

import json
import sys
from dataclasses import asdict

import click
from tabulate import tabulate

from gibr.notify import safe_echo, warning


@click.command("issues")
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output issues in JSON format.",
)
@click.pass_context
def issues(ctx, output_json: bool):
    """List open issues from the tracker."""
    tracker = ctx.obj["tracker"]
    issues = tracker.list_issues()
    if not issues:
        warning("No open issues found.")
        return
    table = [[issue.id, issue.type, issue.title, issue.assignee] for issue in issues]
    if output_json:
        click.echo(json.dumps([asdict(issue) for issue in issues], indent=4))
    else:
        output = tabulate(
            table, headers=["Issue", "Type", "Title", "Assignee"], tablefmt="github"
        )
        if sys.stdout.isatty():
            click.echo_via_pager(output)
        else:
            safe_echo(output)
