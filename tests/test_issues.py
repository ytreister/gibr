"""Tests for the 'issues' CLI command."""

import json
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gibr.cli import cli
from gibr.issue import Issue


def make_mock_config():
    """Return a mock GibrConfig with .config so CLI doesn't crash."""
    cfg = MagicMock()
    cfg.load.return_value = cfg
    cfg.config = {}
    return cfg


@patch("gibr.cli.GibrConfig", return_value=make_mock_config())
@patch("gibr.cli.issues.warning")
@patch("gibr.cli.get_tracker")
def test_issues_no_issues(mock_get_tracker, mock_warning, _):
    """Test that when there are no issues, a warning is shown."""
    runner = CliRunner()

    tracker = mock_get_tracker.return_value
    tracker.list_issues.return_value = []

    result = runner.invoke(cli, ["issues"])

    assert result.exit_code == 0
    mock_warning.assert_called_once_with("No open issues found.")


@patch("gibr.cli.GibrConfig", return_value=make_mock_config())
@patch("gibr.cli.issues.safe_echo")
@patch("gibr.cli.get_tracker")
def test_issues_outputs_table(mock_get_tracker, mock_safe_echo, _):
    """Test that issues are output in table format using safe_echo."""
    runner = CliRunner()

    issue1 = Issue(id=1, title="Bug A", assignee="alice")
    issue2 = Issue(id=2, title="Task B", assignee="bob")

    tracker = mock_get_tracker.return_value
    tracker.list_issues.return_value = [issue1, issue2]

    result = runner.invoke(cli, ["issues"])

    assert result.exit_code == 0
    mock_safe_echo.assert_called_once()


@patch("gibr.cli.GibrConfig", return_value=make_mock_config())
@patch("gibr.cli.issues.click.echo")
@patch("gibr.cli.get_tracker")
def test_issues_outputs_json(mock_get_tracker, mock_echo, _):
    """Test that issues are output in JSON format when --json is used."""
    runner = CliRunner()

    issue = Issue(id=10, title="Bug", assignee="me")
    tracker = mock_get_tracker.return_value
    tracker.list_issues.return_value = [issue]

    result = runner.invoke(cli, ["issues", "--json"])

    assert result.exit_code == 0

    sent_json = mock_echo.call_args[0][0]
    parsed = json.loads(sent_json)

    assert parsed == [{"id": 10, "type": "issue", "title": "Bug", "assignee": "me"}]
