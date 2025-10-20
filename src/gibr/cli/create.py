"""CLI command to create a branch based on an issue number."""

import click

from gibr.branch import BranchName
from gibr.git import create_and_push_branch


@click.command("create")
@click.argument("issue_number")
@click.pass_context
def create(ctx, issue_number):
    """Generate a branch based on the issue number provided."""
    config = ctx.obj["config"]
    tracker = ctx.obj["tracker"]
    issue = tracker.get_issue(issue_number)
    branch_name = BranchName(config.config["DEFAULT"]["branch_name_format"]).generate(
        issue
    )
    click.echo(f"Generating branch name for issue #{issue.id}: {issue.title}")
    click.echo(f"Branch name: {branch_name}")
    create_and_push_branch(branch_name)
