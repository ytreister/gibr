"""Integration tests for the gibr CLI commands."""

import os
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gibr.cli import cli


@patch("gibr.cli.GibrConfig")
@patch("gibr.cli.alias.GitConfigParser")
@patch("gibr.cli.alias.party")
@patch("gibr.cli.alias.success")
@patch("gibr.cli.get_tracker")
def test_alias_command_creates_git_aliases(
    mock_get_tracker, mock_success, mock_party, mock_gitconfig, *_
):
    """Integration test for 'gibr alias' command."""
    runner = CliRunner()

    mock_tracker = MagicMock()
    mock_get_tracker.return_value = mock_tracker

    mock_parser = MagicMock()
    mock_gitconfig.return_value = mock_parser

    result = runner.invoke(cli, ["alias"])

    assert result.exit_code == 0
    mock_gitconfig.assert_called_once_with(
        os.path.expanduser("~/.gitconfig"), read_only=False
    )
    mock_parser.set_value.assert_called()
    mock_parser.write.assert_called_once()
    mock_party.assert_called_once_with("Git aliases successfully added!")
    mock_success.assert_any_call("Added git alias: git create → !gibr git create")
    mock_success.assert_any_call("Added git alias: git issues → !gibr git issues")


@patch("gibr.git.success")
@patch("gibr.git.Repo")
@patch("gibr.cli.get_tracker")
@patch("gibr.cli.GibrConfig")
def test_create_command_creates_branch_and_pushes_to_origin(
    mock_config, mock_get_tracker, mock_repo, mock_success
):
    """Integration test for 'gibr create <issue_number>' command."""
    runner = CliRunner()

    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = False
    mock_repo.return_value = mock_repo

    mock_tracker = MagicMock()
    mock_issue = MagicMock(
        id=17, title="Fix login bug", type="issue", sanitized_title="fix-login-bug"
    )
    mock_tracker.get_issue.return_value = mock_issue
    mock_get_tracker.return_value = mock_tracker

    mock_config.return_value.load.return_value = mock_config.return_value
    mock_config.return_value.config = {
        "DEFAULT": {"branch_name_format": "{issue}-{title}"}
    }

    result = runner.invoke(cli, ["create", "17"])

    assert result.exit_code == 0
    print(mock_success.call_args_list)
    mock_success.assert_any_call("Checked out branch: 17-fix-login-bug")
    mock_success.assert_any_call("Pushed branch '17-fix-login-bug' to origin.")


@patch("gibr.cli.get_tracker")
@patch("gibr.cli.GibrConfig")
@patch("gibr.git.warning")
@patch("gibr.git.Repo")
def test_create_command_dirty_repo(mock_repo, mock_warning, *_):
    """Integration test for 'gibr create <issue_number>' when repo is dirty."""
    runner = CliRunner()

    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = True
    mock_repo.return_value = mock_repo
    result = runner.invoke(cli, ["create", "42"])

    assert result.exit_code == 0
    mock_warning.assert_any_call("Working tree is dirty — uncommitted changes present.")


def test_cli_shows_help():
    """Basic test to ensure CLI runs and shows top-level help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output
    assert "Commands" in result.output


def test_cli_fails_on_unknown_command():
    """Ensure an invalid command exits with nonzero code."""
    runner = CliRunner()
    result = runner.invoke(cli, ["nonexistent"])
    assert result.exit_code != 0
    assert "No such command" in result.output
