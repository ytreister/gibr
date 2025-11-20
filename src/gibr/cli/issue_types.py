"""CLI command to map issue types ."""

import click

from gibr import notify


@click.command("issue-types")
@click.pass_context
def issue_types(ctx):
    """Initialize gibr configuration interactively."""
    tracker = ctx.obj["tracker"]
    if not tracker.issue_types_supported:
        notify.error(f"{tracker.display_name} does not support issue types.")
    click.echo(f"Detected tracker: {tracker.display_name}")
    click.echo("Fetching labels...\n")
    labels = tracker.get_labels()
    click.echo(f"Found {len(labels)} labels:\n")
    for i, labels in enumerate(labels, start=1):
        click.echo(f"  {i}. {labels}")
    selected_labels = click.prompt(
        "\nWHich labels represent ISSUE TYPES (comma-separated)",
        default="",
    )
    if selected_labels.strip() == "":
        notify.warning("No labels selected. Operation canceled.")
        return
    print(selected_labels)
