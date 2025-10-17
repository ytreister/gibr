"""CLI for gibr."""

import logging

import click

from gibr.config import GibrConfig
from gibr.logger import configure_logger


@click.command()
@click.argument("issue_number")
@click.option("--verbose", is_flag=True, help="Turn on verbose logging")
def app(issue_number, verbose):
    """Generate a branch based on the issue number provided."""
    configure_logger(verbose)
    config = GibrConfig().load()
    logging.info(f"Generating branch name for issue #{issue_number}")
