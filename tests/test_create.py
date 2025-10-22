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
