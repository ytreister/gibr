"""CLI for gibr."""

import logging

import click

from gibr.config import GibrConfig
from gibr.factory import get_tracker
from gibr.logger import configure_logger
from gibr.notify import warning

from .alias import alias
from .create import create
from .group import GibrGroup
from .init import init
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
    if ctx.invoked_subcommand == "init":
        logging.debug("Skipping config loading for init command.")
        return
    try:
        config = GibrConfig().load()
        ctx.obj["config"] = config
        ctx.obj["tracker"] = get_tracker(config.config)
    except FileNotFoundError as e:
        warning(str(e))
        click.echo("👉 Run `gibr init` to create a new configuration file.\n")
        if click.confirm("Would you like to run `gibr init` now?", default=True):
            ctx.invoke(init)
        ctx.exit(0)


cli.add_command(create)
cli.add_command(issues)
cli.add_command(alias)
cli.add_command(init)
