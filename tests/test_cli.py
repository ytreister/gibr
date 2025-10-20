"""Integration tests for the gibr CLI commands."""

import os
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gibr.cli import cli


@patch("gibr.cli.get_tracker", return_value=MagicMock())
@patch("gibr.cli.alias.success", return_value=None)
@patch("gibr.cli.alias.party", return_value=None)
@patch("gibr.cli.alias.GitConfigParser", return_value=MagicMock())
@patch("gibr.cli.GibrConfig", return_value=MagicMock())
def test_alias_command_creates_git_aliases(
    _mock_gibr_config,
    mock_gitconfig,
    mock_party,
    mock_success,
    _mock_get_tracker,
):
    """Integration test for 'gibr alias' command."""
    runner = CliRunner()

    result = runner.invoke(cli, ["alias"])
    assert result.exit_code == 0

    # Assertions
    mock_gitconfig.assert_called_once_with(
        os.path.expanduser("~/.gitconfig"), read_only=False
    )
    parser = mock_gitconfig.return_value
    parser.set_value.assert_called()
    parser.write.assert_called_once()

    mock_party.assert_called_once_with("Git aliases successfully added!")
    mock_success.assert_any_call("Added git alias: git create → !gibr git create")
    mock_success.assert_any_call("Added git alias: git issues → !gibr git issues")


@patch("gibr.git.success", return_value=None)
@patch("gibr.git.Repo", return_value=MagicMock())
@patch("gibr.cli.get_tracker", return_value=MagicMock())
@patch("gibr.cli.GibrConfig", return_value=MagicMock())
def test_create_command_creates_branch_and_pushes_to_origin(
    mock_config,
    mock_get_tracker,
    mock_repo,
    mock_success,
):
    """Integration test for 'gibr create <issue_number>' command."""
    runner = CliRunner()

    repo_instance = mock_repo.return_value
    repo_instance.is_dirty.return_value = False

    # Mock tracker + issue
    tracker_instance = mock_get_tracker.return_value
    issue = MagicMock(
        id=17, title="Fix login bug", type="issue", sanitized_title="fix-login-bug"
    )
    tracker_instance.get_issue.return_value = issue

    # Mock config
    cfg_instance = mock_config.return_value
    cfg_instance.load.return_value = cfg_instance
    cfg_instance.config = {"DEFAULT": {"branch_name_format": "{issue}-{title}"}}

    result = runner.invoke(cli, ["create", "17"])
    assert result.exit_code == 0

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


@patch("click.confirm", return_value=False)
@patch("gibr.cli.warning")
@patch("gibr.cli.GibrConfig")
def test_file_not_found_shows_init_prompt(
    mock_gibr_config, mock_warning, _mock_confirm
):
    """When the config file is missing, CLI should warn and suggest `gibr init`."""
    runner = CliRunner()

    mock_cfg = MagicMock()
    mock_cfg.load.side_effect = FileNotFoundError("config file not found")
    mock_gibr_config.return_value = mock_cfg

    result = runner.invoke(cli, ["create", "1"])

    assert result.exit_code == 0
    mock_warning.assert_called_once_with("config file not found")
    assert "Run `gibr init` to create a new configuration file." in result.output


@patch("gibr.cli.init")
@patch("click.confirm", return_value=True)
@patch("gibr.cli.warning")
@patch("gibr.cli.GibrConfig")
def test_file_not_found_runs_init_when_user_confirms(
    mock_gibr_config, mock_warning, _mock_confirm, mock_init
):
    """When config file is missing and user agrees, CLI should invoke `gibr init`."""
    runner = CliRunner()

    mock_cfg = MagicMock()
    mock_cfg.load.side_effect = FileNotFoundError("config file not found")
    mock_gibr_config.return_value = mock_cfg

    result = runner.invoke(cli, ["create", "1"])

    assert result.exit_code == 0
    mock_warning.assert_called_once_with("config file not found")

    # Verify the init command was invoked
    mock_init.assert_called_once()


@patch("gibr.cli.logging.debug")
@patch("gibr.cli.get_tracker")
@patch("gibr.cli.GibrConfig")
def test_init_command_skips_config_loading(
    mock_gibr_config, mock_get_tracker, mock_debug
):
    """The 'init' command should skip config loading and log the debug message."""
    runner = CliRunner()

    # Run the CLI with the `init` subcommand
    runner.invoke(cli, ["init"])

    # Verify config and tracker loading were NOT called
    mock_gibr_config.assert_not_called()
    mock_get_tracker.assert_not_called()

    # Verify the debug message was logged
    mock_debug.assert_any_call("Skipping config loading for init command.")
