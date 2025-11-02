"""CLI command to list open issues from the tracker."""

import click
from tabulate import tabulate

from gibr.notify import warning


@click.command("issues")
@click.pass_context
def issues(ctx):
    """List open issues from the tracker."""
    tracker = ctx.obj["tracker"]
    issues = tracker.list_issues()
    if not issues:
        warning("No open issues found.")
        return
    table = [[issue.id, issue.type, issue.title, issue.assignee] for issue in issues]

    click.echo(
        tabulate(
            table, headers=["Issue", "Type", "Title", "Assignee"], tablefmt="github"
        )
    )
