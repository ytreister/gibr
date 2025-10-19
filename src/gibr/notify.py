"""Error classes for Gibr."""

import click


def info(msg):
    """Display an informational message."""
    click.secho(f"ℹ️  {msg}", fg="blue")


def success(msg):
    """Display a success message."""
    click.secho(f"✅  {msg}", fg="green", bold=True)


def warning(msg):
    """Display a warning message."""
    click.secho(f"⚠️  {msg}", fg="yellow")


def error(msg):
    """Display an error message."""
    click.secho(f"❌  {msg}", fg="red", bold=True)
