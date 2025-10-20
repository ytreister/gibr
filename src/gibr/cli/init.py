"""CLI command to initialize gibr configuration interactively."""

import configparser
import os
from pathlib import Path

import click

from gibr.notify import party, success, warning

TRACKERS = {
    "1": ("GitHub", True),
    "2": ("Jira", True),
    "3": ("GitLab", False),
    "4": ("Linear", False),
    "5": ("Monday.com", False),
}


def check_token(var_name: str, service_name: str) -> str:
    """Check if a token exists in env or prompt to create it."""
    token = os.getenv(var_name)
    if token:
        party(f"Found {service_name} token in environment ({var_name})")
        return

    warning(f"No {service_name} token found in environment ({var_name}).")
    click.echo("You can set it by running:")
    click.echo(f'  export {var_name}="your_token_here"  (macOS/Linux)')
    click.echo(f'  setx {var_name} "your_token_here"     (Windows)\n')


@click.command("init")
def init():
    """Initialize gibr configuration interactively."""
    click.echo("Welcome to gibr setup! Let’s get you started 🚀\n")

    click.echo("Which issue tracker do you use?")
    for k, (name, supported) in TRACKERS.items():
        label = name if supported else f"{name} (coming soon)"
        click.echo(f"{k}. {label}")

    choice = click.prompt(
        "\nSelect a number", default="1", type=click.Choice(TRACKERS.keys())
    )

    tracker_name, supported = TRACKERS[choice]
    if not supported:
        warning(f"{tracker_name} support is coming soon — stay tuned!")
        return
    tracker_key = tracker_name.lower().replace(".", "").replace(" ", "")

    click.echo(f"\n{tracker_name} selected.\n")

    config = configparser.ConfigParser()
    config["DEFAULT"] = {"branch_name_format": "{issue}-{title}"}
    config["issue-tracker"] = {"name": tracker_key}

    if tracker_key == "github":
        repo = click.prompt("GitHub repository (e.g. user/repo)")
        token_var = click.prompt(
            "Environment variable for your GitHub token", default="GITHUB_TOKEN"
        )
        check_token(token_var, tracker_name)
        config["github"] = {"repo": repo, "token": f"${{{token_var}}}"}

    elif tracker_key == "jira":
        url = click.prompt("Jira base URL (e.g. https://company.atlassian.net)")
        project_key = click.prompt("Jira project key (e.g. PROJ)")
        user = click.prompt("Jira username/email")
        token_var = click.prompt(
            "Environment variable for your Jira token", default="JIRA_TOKEN"
        )
        check_token(token_var, tracker_name)

        config["jira"] = {
            "url": url,
            "project_key": project_key,
            "user": user,
            "token": f"${{{token_var}}}",
        }

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

    success(f"Created {path} with {tracker_name} settings")
    click.secho("You're all set! Try: `gibr issues`\n", fg="cyan")
