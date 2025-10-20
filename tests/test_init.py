"""Tests for init command."""

import os
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from gibr.cli.init import check_token, init


@patch("gibr.cli.init.party")
@patch.dict(os.environ, {"GITHUB_TOKEN": "abc123"})
def test_check_token_found(mock_party):
    """Should call party() when token is found in env."""
    check_token("GITHUB_TOKEN", "GitHub")
    mock_party.assert_called_once()
    assert "GitHub token in environment" in mock_party.call_args[0][0]


@patch("gibr.cli.init.warning")
@patch.dict(os.environ, {}, clear=True)
def test_check_token_missing(mock_warning, capsys):
    """Should warn and print export instructions when token missing."""
    check_token("GITHUB_TOKEN", "GitHub")

    mock_warning.assert_called_once()
    out = capsys.readouterr().out
    assert "export GITHUB_TOKEN" in out
    assert "setx GITHUB_TOKEN" in out


@patch("gibr.cli.init.check_token", return_value=None)
@patch("click.prompt", side_effect=["1", "user/repo", "GITHUB_TOKEN"])
@patch("click.confirm", return_value=True)
def test_init_github_creates_config(
    _mock_confirm,
    _mock_prompt,
    _mock_check_token,
    tmp_path,
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


@patch("gibr.cli.init.check_token", return_value=None)
@patch(
    "click.prompt",
    side_effect=[
        "2",
        "https://company.atlassian.net",
        "PROJ",
        "me@company.com",
        "JIRA_API_TOKEN",
    ],
)
@patch("click.confirm", return_value=True)
def test_init_jira_creates_config(
    _mock_confirm, _mock_prompt, _mock_check_token, tmp_path
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


@patch("gibr.cli.init.warning")
@patch("gibr.cli.init.check_token", return_value=None)
@patch("click.prompt", side_effect=["1", "user/repo", "GITHUB_TOKEN"])
@patch("click.confirm", return_value=False)
def test_init_overwrite_decline(
    _mock_confirm, _mock_prompt, _mock_check_token, mock_warning, tmp_path
):
    """Should not overwrite existing file if user declines."""
    runner = CliRunner()
    with runner.isolated_filesystem(tmp_path):
        cfg = Path(".gibrconfig")
        cfg.write_text("[default]\n")

        result = runner.invoke(init)
        assert result.exit_code == 0

        assert "Operation canceled" in mock_warning.call_args[0][0]
        assert cfg.read_text() == "[default]\n"


@patch("gibr.cli.init.warning")
@patch("click.prompt", side_effect=["3"])
def test_init_unsupported_tracker(_mock_prompt, mock_warning, tmp_path):
    """Should warn and exit for unsupported tracker."""
    runner = CliRunner()
    with runner.isolated_filesystem(tmp_path):
        result = runner.invoke(init)
        assert result.exit_code == 0
        mock_warning.assert_called_once()
        assert "coming soon" in mock_warning.call_args[0][0]
        assert not Path(".gibrconfig").exists()
