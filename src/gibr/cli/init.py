"""CLI command to initialize gibr configuration interactively."""

import configparser
from pathlib import Path

import click

from gibr.notify import success, warning
from gibr.registry import TRACKER_REGISTRY


@click.command("init")
def init():
    """Initialize gibr configuration interactively."""
    click.echo("Welcome to gibr setup! Let’s get you started 🚀\n")

    click.echo("Which issue tracker do you use?")
    supported_trackers = {k: v for k, v in TRACKER_REGISTRY.items() if v["supported"]}
    unsupported_trackers = {
        k: v for k, v in TRACKER_REGISTRY.items() if not v["supported"]
    }
    options = list(supported_trackers.items()) + list(unsupported_trackers.items())
    for i, (key, info) in enumerate(options, 1):
        label = info["display_name"]
        if not info["supported"]:
            label += " (coming soon)"
        click.echo(f"{i}. {label}")

    choice = click.prompt(
        "\nSelect a number",
        default="1",
        type=click.Choice([str(i) for i in range(1, len(options) + 1)]),
    )
    choice = int(choice)

    tracker_key, info = options[choice - 1]
    if not info["supported"]:
        warning(f"{info['display_name']} support is coming soon — stay tuned!")
        return

    tracker_cls = info["class"]
    click.echo(f"\n{tracker_cls.display_name} selected.\n")

    config = configparser.ConfigParser()
    config["DEFAULT"] = {"branch_name_format": "{issue}-{title}"}
    config["issue-tracker"] = {"name": tracker_key}
    config[tracker_key] = tracker_cls.configure_interactively()

    path = Path(".gibrconfig")
    if path.exists():
        overwrite = click.confirm(
            ".gibrconfig already exists. Overwrite?", default=False
        )
        if not overwrite:
            warning("Operation canceled.")
            return

    with open(path, "w") as f:
        config.write(f)

    success(f"Created {path} with {info['display_name']} settings")
    click.secho("You're all set! Try: `gibr issues`\n", fg="cyan")
