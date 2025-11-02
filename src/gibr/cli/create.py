"""CLI command to create a branch based on an issue number."""

import click

from gibr.branch import BranchName
from gibr.git import create_and_push_branch
from gibr.notify import error


@click.command("create")
@click.argument("issue_number")
@click.pass_context
def create(ctx, issue_number):
    """Generate a branch based on the issue number provided."""
    config = ctx.obj["config"]
    tracker = ctx.obj["tracker"]
    if tracker.numeric_issues and not issue_number.isdigit():
        error(f"Issue number must be numeric for {tracker.display_name} issue tracker.")

    issue = tracker.get_issue(issue_number)
    branch_name_format = config.config["DEFAULT"]["branch_name_format"]

    # TODO In the future, instead of setting an error here, we should ask if
    # they want to assign the issue to the current user
    if not issue.assignee and "{assignee}" in branch_name_format:
        error(
            "Can't create branch, issue has no assignee and branch format requires it"
        )
    branch_name = BranchName(config.config["DEFAULT"]["branch_name_format"]).generate(
        issue
    )
    click.echo(f"Generating branch name for issue #{issue.id}: {issue.title}")
    click.echo(f"Branch name: {branch_name}")
    create_and_push_branch(branch_name)
