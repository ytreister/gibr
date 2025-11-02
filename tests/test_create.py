"""Tests for the create command."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from gibr.cli.create import create


@patch("gibr.cli.create.error", side_effect=None)
def test_create_non_jira_tracker_with_non_digit_issue(mock_error):
    """Should call error if non-digit issue number is used with non-Jira tracker."""
    mock_config = MagicMock()
    mock_config.config = {"DEFAULT": {"branch_name_format": "{id}-{title}"}}
    mock_tracker = MagicMock(display_name="GitHub")

    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(
            create,
            ["ABC-123"],
            obj={"config": mock_config, "tracker": mock_tracker},
        )

    mock_error.assert_called_once_with(
        "Issue number must be numeric for GitHub issue tracker."
    )


@patch("gibr.cli.create.error", side_effect=None)
def test_create_with_missing_assignee_and_assignee_in_format(mock_error):
    """Should call error if issue has no assignee but format includes {assignee}."""
    mock_config = MagicMock()
    mock_config.config = {
        "DEFAULT": {"branch_name_format": "{issue}-{assignee}-{title}"}
    }

    mock_issue = MagicMock(id=123, title="Fix login bug", assignee=None)
    mock_tracker = MagicMock()
    mock_tracker.numeric_issues = True
    mock_tracker.get_issue.return_value = mock_issue
    mock_tracker.display_name = "GitLab"

    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(
            create,
            ["123"],
            obj={"config": mock_config, "tracker": mock_tracker},
        )

    mock_error.assert_called_once_with(
        "Can't create branch, issue has no assignee and branch format requires it"
    )


@patch("gibr.cli.create.create_and_push_branch")
@patch("gibr.cli.create.click.echo")
def test_create_with_missing_assignee_but_no_assignee_in_format(mock_echo, mock_branch):
    """Should succeed when assignee missing but not required in format."""
    mock_config = MagicMock()
    mock_config.config = {"DEFAULT": {"branch_name_format": "{issue}-{title}"}}

    mock_issue = MagicMock(id=456, title="Add dark mode", assignee=None)
    mock_tracker = MagicMock()
    mock_tracker.numeric_issues = True
    mock_tracker.get_issue.return_value = mock_issue

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            create,
            ["456"],
            obj={"config": mock_config, "tracker": mock_tracker},
        )

    assert result.exit_code == 0
    mock_branch.assert_called_once()
    mock_echo.assert_any_call("Generating branch name for issue #456: Add dark mode")
