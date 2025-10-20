"""Tests for gibr.config."""

from textwrap import dedent
from unittest.mock import MagicMock, patch

import pytest

from gibr.config import EnvInterpolation, GibrConfig


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary .gibrconfig file for testing."""
    cfg_content = dedent("""
        [DEFAULT]
        branch_name_format = feat/{issue_id}-{summary}

        [issue-tracker]
        name = github

        [github]
        repo = ytreister/gibr
        token = ghp_testtoken
    """)
    cfg_path = tmp_path / ".gibrconfig"
    cfg_path.write_text(cfg_content)
    return cfg_path


def test_env_interpolation_expands_env_vars():
    """EnvInterpolation should expand environment variables."""
    with patch.dict("os.environ", {"TOKEN_VAR": "supersecret"}):
        interp = EnvInterpolation()
        parser = MagicMock()
        value = interp.before_get(parser, "s", "o", "Value=$TOKEN_VAR", {})
        assert value == "Value=supersecret"


def test_find_config_file_finds_in_current_dir(temp_config_file):
    """_find_config_file should return path to .gibrconfig in current dir."""
    with patch("pathlib.Path.cwd", return_value=temp_config_file.parent):
        g = GibrConfig()
        result = g._find_config_file()
        assert result == temp_config_file


def test_find_config_file_finds_in_parent_dir(temp_config_file):
    """_find_config_file should walk up parent dirs until found."""
    child_dir = temp_config_file.parent / "subdir"
    child_dir.mkdir()
    with patch("pathlib.Path.cwd", return_value=child_dir):
        g = GibrConfig()
        result = g._find_config_file()
        assert result == temp_config_file


@patch("gibr.config.error")
def test_load_no_config_file_calls_error(mock_error):
    """load() should call error() when config file is not found."""
    with patch.object(GibrConfig, "_find_config_file", return_value=None):
        mock_error.side_effect = SystemExit  # mimic click.Abort
        g = GibrConfig()
        with pytest.raises(SystemExit):
            g.load()
        mock_error.assert_called_once_with(
            ".gibrconfig not found in this or any parent directory"
        )


@patch("gibr.config.ConfigParser")
def test_load_reads_config_and_sets_attributes(mock_parser_cls, temp_config_file):
    """load() should populate config dict correctly."""
    mock_parser = mock_parser_cls.return_value
    mock_parser.sections.return_value = ["issue-tracker", "github"]
    mock_parser.items.side_effect = (
        lambda section: [
            ("name", "github"),
        ]
        if section == "issue-tracker"
        else [
            ("repo", "ytreister/gibr"),
            ("token", "ghp_testtoken"),
        ]
    )
    mock_parser.defaults.return_value = {"branch_name_format": "feat/{id}-{summary}"}

    with patch.object(GibrConfig, "_find_config_file", return_value=temp_config_file):
        g = GibrConfig()
        result = g.load()
        assert result is g
        assert "issue-tracker" in g.config
        assert g.config["github"]["repo"] == "ytreister/gibr"


def test_str_outputs_expected_for_github_config(temp_config_file):
    """__str__ should include GitHub details when tracker is github."""
    g = GibrConfig()
    with patch.object(GibrConfig, "_find_config_file", return_value=temp_config_file):
        g.load()
    output = str(g)
    assert "Github:" in output
    assert "ytreister/gibr" in output
    assert "ghp_testtoken" in output


def test_str_outputs_expected_for_jira_config(tmp_path):
    """__str__ should include Jira details when tracker is jira."""
    cfg_content = dedent("""
        [issue-tracker]
        name = jira

        [jira]
        url = https://example.atlassian.net
        project_key = TEST
        user = alice
        token = abc123
    """)
    cfg_file = tmp_path / ".gibrconfig"
    cfg_file.write_text(cfg_content)

    g = GibrConfig()
    with patch.object(GibrConfig, "_find_config_file", return_value=cfg_file):
        g.load()
    output = str(g)
    assert "Jira:" in output
    assert "example.atlassian.net" in output
    assert "TEST" in output
