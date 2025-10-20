"""CLI for gibr."""

import logging

import click

from gibr.config import GibrConfig
from gibr.logger import configure_logger
from gibr.trackers.factory import get_tracker

from .alias import alias
from .create import create
from .group import GibrGroup
from .issues import issues


@click.group(cls=GibrGroup)
@click.option("--verbose", is_flag=True, help="Turn on verbose logging")
@click.pass_context
def cli(ctx, verbose):
    """GIBR — streamline your git branch creation workflow."""
    # Configure logging and echo verbose mode
    configure_logger(verbose)
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    logging.debug("Verbose modes enabled.")

    # Initialize shared config and tracker once
    config = GibrConfig().load()
    ctx.obj["config"] = config
    ctx.obj["tracker"] = get_tracker(config.config)


cli.add_command(create)
cli.add_command(issues)
cli.add_command(alias)
