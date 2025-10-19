"""Utility functions for displaying notifications in the CLI using Click."""

import click


def info(msg):
    """Display an informational message."""
    click.secho(f"ℹ️  {msg}", fg="blue")


def success(msg):
    """Display a success message."""
    click.secho(f"✅  {msg}", fg="green", bold=True)


def party(msg):
    """Display a celebratory message."""
    click.secho(f"🎉  {msg}", fg="magenta", bold=True)


def warning(msg):
    """Display a warning message."""
    click.secho(f"⚠️  {msg}", fg="yellow")


def error(msg):
    """Display an error message."""
    click.secho(f"❌  {msg}", fg="red", bold=True)
    raise click.Abort()
