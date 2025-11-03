"""Tests for init command."""

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from gibr.cli.init import init


@patch(
    "gibr.trackers.github.GithubTracker.configure_interactively",
    return_value={"repo": "user/repo", "token": "${GITHUB_TOKEN}"},
)
@patch("click.confirm", return_value=True)
@patch("click.prompt", side_effect=["2"])
def test_init_github_creates_config(
    _mock_prompt, _mock_confirm, _mock_configure, tmp_path
):
    """Should create .gibrconfig with GitHub settings."""
    runner = CliRunner()
    with runner.isolated_filesystem(tmp_path):
        result = runner.invoke(init)
        assert result.exit_code == 0

        cfg = Path(".gibrconfig")
        assert cfg.exists()

        content = cfg.read_text()
        assert "github" in content
        assert "repo = user/repo" in content
        assert "token = ${GITHUB_TOKEN}" in content


@patch(
    "gibr.trackers.jira.JiraTracker.configure_interactively",
    return_value={
        "url": "https://company.atlassian.net",
        "project_key": "PROJ",
        "user": "me@company.com",
        "token": "${JIRA_API_TOKEN}",
    },
)
@patch("click.confirm", return_value=True)
@patch("click.prompt", side_effect=["4"])
def test_init_jira_creates_config(
    _mock_prompt, _mock_confirm, _mock_configure, tmp_path
):
    """Should create .gibrconfig with Jira settings."""
    runner = CliRunner()
    with runner.isolated_filesystem(tmp_path):
        result = runner.invoke(init)
        assert result.exit_code == 0

        cfg = Path(".gibrconfig")
        assert cfg.exists()

        content = cfg.read_text()
        assert "jira" in content
        assert "url = https://company.atlassian.net" in content
        assert "project_key = PROJ" in content
        assert "user = me@company.com" in content
        assert "token = ${JIRA_API_TOKEN}" in content


@patch("click.prompt", side_effect=["6"])
@patch("gibr.cli.init.warning")
def test_init_unsupported_tracker(_mock_warning, _mock_prompt, tmp_path):
    """Should warn and exit for unsupported tracker."""
    runner = CliRunner()
    with runner.isolated_filesystem(tmp_path):
        result = runner.invoke(init)
        assert result.exit_code == 0
        _mock_warning.assert_called_once()
        assert "coming soon" in _mock_warning.call_args[0][0]
        assert not Path(".gibrconfig").exists()


@patch("click.prompt", side_effect=["2"])
@patch("click.confirm", return_value=False)
@patch(
    "gibr.trackers.github.GithubTracker.configure_interactively",
    return_value={
        "repo": "user/repo",
        "token": "${GITHUB_TOKEN}",
    },
)
@patch("gibr.cli.init.warning")
def test_init_overwrite_decline(
    _mock_warning, _mock_configure, _mock_confirm, _mock_prompt, tmp_path
):
    """Should not overwrite existing file if user declines."""
    runner = CliRunner()
    with runner.isolated_filesystem(tmp_path):
        cfg = Path(".gibrconfig")
        cfg.write_text("[default]\n")

        result = runner.invoke(init)
        assert result.exit_code == 0
        _mock_warning.assert_called_once()
        assert "Operation canceled" in _mock_warning.call_args[0][0]
        assert cfg.read_text() == "[default]\n"
