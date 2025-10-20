"""CLI command to add git aliases for gibr commands."""

import os

import click
from git import GitConfigParser

from gibr.notify import party, success

DO_NOT_ALIAS = ["alias", "init"]


@click.command("alias")
@click.pass_context
def alias(ctx):
    """Add git aliases for gibr commands."""
    commands = [
        name
        for name, cmd in ctx.parent.command.commands.items()
        if name not in DO_NOT_ALIAS
    ]

    try:
        config = GitConfigParser(os.path.expanduser("~/.gitconfig"), read_only=False)
        for name in commands:
            cmd = f"!gibr git {name}"
            config.set_value("alias", name, cmd)
            success(f"Added git alias: git {name} → {cmd}")
        config.write()
        party("Git aliases successfully added!")
    except Exception as e:
        raise click.ClickException(f"Failed to set git aliases: {e}")
