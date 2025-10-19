"""CLI for gibr."""

import logging

import click

from gibr.branch import BranchName
from gibr.config import GibrConfig
from gibr.git import create_and_push_branch
from gibr.logger import configure_logger
from gibr.trackers.factory import get_tracker


class GibrGroup(click.Group):
    """Custom Click group that treats 'gibr <issue_number>' like 'gibr create <issue_number>'."""

    def parse_args(self, ctx, args):
        """Preprocess args to handle 'gibr <issue_number>' as 'gibr create <issue_number>'."""
        for i, arg in enumerate(args):
            if not arg.startswith("--"):
                if arg.isdigit() and arg not in self.commands:
                    args.insert(i, "create")
                break
        return super().parse_args(ctx, args)


@click.group(cls=GibrGroup)
@click.option("--verbose", is_flag=True, help="Turn on verbose logging")
@click.pass_context
def cli(ctx, verbose):
    """Gibr — streamline your git + issue tracker workflow."""
    # Configure logging and echo verbose mode
    configure_logger(verbose)
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    logging.debug("Verbose modes enabled.")

    # Initialize shared config and tracker once
    config = GibrConfig().load()
    ctx.obj["config"] = config
    ctx.obj["tracker"] = get_tracker(config.config)


@cli.command("create")
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


@cli.command("issues")
@click.pass_context
def issues(ctx):
    """List open issues from the tracker."""
    tracker = ctx.obj["tracker"]
    issues = tracker.list_issues()
    for issue in issues:
        click.echo(f"#{issue.id} — {issue.title}")


if __name__ == "__main__":
    cli()
