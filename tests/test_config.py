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
        name = fake

        [fake]
        foo = bar
        baz = qux
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


def test_load_no_config_file_raises_file_not_found():
    """load() should raise FileNotFoundError when config file is not found."""
    with patch.object(GibrConfig, "_find_config_file", return_value=None):
        g = GibrConfig()
        with pytest.raises(FileNotFoundError) as excinfo:
            g.load()
        assert ".gibrconfig not found" in str(excinfo.value)


@patch("gibr.config.ConfigParser", return_value=MagicMock())
@patch.object(GibrConfig, "_find_config_file")
def test_load_reads_config_and_sets_attributes(
    mock_find_file, mock_parser, temp_config_file
):
    """load() should populate config dict correctly."""
    mock_find_file.return_value = temp_config_file
    parser_instance = mock_parser.return_value

    parser_instance.sections.return_value = ["issue-tracker", "fake"]
    parser_instance.items.side_effect = (
        lambda section: [("name", "fake")]
        if section == "issue-tracker"
        else [("foo", "bar"), ("baz", "qux")]
    )
    parser_instance.defaults.return_value = {
        "branch_name_format": "feat/{id}-{summary}"
    }

    g = GibrConfig()
    result = g.load()

    assert result is g
    assert "issue-tracker" in g.config
    assert g.config["fake"]["foo"] == "bar"


@patch("gibr.config.get_tracker_class")
def test_get_tracker_details_str_with_describe_config(
    mock_get_tracker_class, temp_config_file
):
    """_get_tracker_details_str should use describe_config() when available."""
    g = GibrConfig()
    g.config = {
        "issue-tracker": {"name": "fake"},
        "fake": {"foo": "bar"},
    }

    fake_cls = MagicMock()
    fake_cls.describe_config.return_value = "Description from tracker"
    mock_get_tracker_class.return_value = fake_cls

    result = g._get_tracker_details_str()
    assert "Description from tracker" in result
    mock_get_tracker_class.assert_called_once_with("fake")


@patch("gibr.config.get_tracker_class")
def test_get_tracker_details_str_no_describe_config(mock_get_tracker_class):
    """_get_tracker_details_str should handle tracker without describe_config()."""
    g = GibrConfig()
    g.config = {"issue-tracker": {"name": "generic"}}

    fake_cls = MagicMock()
    del fake_cls.describe_config  # ensure no describe_config method
    fake_cls.__name__ = "GenericTracker"
    mock_get_tracker_class.return_value = fake_cls

    result = g._get_tracker_details_str()
    assert "GenericTracker" in result
    assert "(no describe_config()" in result


@patch("gibr.config.get_tracker_class", side_effect=ValueError)
def test_get_tracker_details_str_unknown_tracker(mock_get_tracker_class):
    """_get_tracker_details_str should return 'Unknown tracker' message."""
    g = GibrConfig()
    g.config = {"issue-tracker": {"name": "unknown"}}
    result = g._get_tracker_details_str()
    assert "Unknown tracker: unknown" in result


def test_str_includes_expected_sections():
    """__str__ should include default and issue-tracker details."""
    g = GibrConfig()
    g.config = {
        "DEFAULT": {"branch_name_format": "feat/{id}"},
        "issue-tracker": {"name": "fake"},
    }
    with patch.object(g, "_get_tracker_details_str", return_value="Fake details"):
        output = str(g)
        assert "Branch Name Format" in output
        assert "fake" in output
        assert "Fake details" in output
