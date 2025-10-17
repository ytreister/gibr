"""CLI for gibr."""

import logging

import click

from gibr.branch import BranchName
from gibr.config import GibrConfig
from gibr.error import IssueNotFoundError
from gibr.git import create_and_push_branch
from gibr.logger import configure_logger
from gibr.trackers.factory import get_tracker


@click.command()
@click.argument("issue_number")
@click.option("--verbose", is_flag=True, help="Turn on verbose logging")
def app(issue_number, verbose):
    """Generate a branch based on the issue number provided."""
    configure_logger(verbose)
    config = GibrConfig().load()
    tracker = get_tracker(config.config)
    try:
        issue = tracker.get_issue(issue_number)
    except IssueNotFoundError as e:
        raise click.ClickException(str(e))
    branch_name = BranchName(config.config["DEFAULT"]["branch_name_format"]).generate(
        issue
    )
    logging.info(f"Generating branch name for issue #{issue.id}: {issue.title}")
    logging.info(f"Branch name: {branch_name}")
    create_and_push_branch(branch_name)
