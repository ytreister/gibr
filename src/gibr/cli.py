"""CLI for gibr"""

import click


@click.command()
@click.argument("issue_number")
def app(issue_number):
    """Generate a branch based on the issue number provided."""
    click.echo(f"Generating branch name for issue #{issue_number}")
