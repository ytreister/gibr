"""Tests for gibr.factory module."""

from unittest.mock import MagicMock, patch

import pytest

import gibr.factory


@pytest.mark.parametrize(
    "bad_config",
    [
        {},  # completely missing 'issue-tracker'
        {"issue-tracker": {}},  # missing 'name' inside
    ],
)
def test_get_tracker_raises_valueerror_if_missing_name(bad_config):
    """get_tracker should raise ValueError when config lacks issue-tracker.name."""
    with pytest.raises(ValueError) as excinfo:
        gibr.factory.get_tracker(bad_config)

    assert "Missing 'issue-tracker.name' in config." in str(excinfo.value)


@patch("gibr.factory.get_tracker_class")
def test_get_tracker_calls_from_config_and_returns_instance(mock_get_tracker_class):
    """get_tracker should call tracker_cls.from_config() and return its value."""
    fake_tracker_instance = object()
    fake_tracker_cls = MagicMock()
    fake_tracker_cls.__name__ = "FakeTracker"
    fake_tracker_cls.from_config.return_value = fake_tracker_instance

    mock_get_tracker_class.return_value = fake_tracker_cls

    config = {
        "issue-tracker": {"name": "somekey"},
        "somekey": {"foo": "bar"},
    }

    result = gibr.factory.get_tracker(config)

    mock_get_tracker_class.assert_called_once_with("somekey")
    fake_tracker_cls.from_config.assert_called_once_with(config["somekey"])
    assert result is fake_tracker_instance


@patch("gibr.factory.get_tracker_class")
def test_get_tracker_raises_if_no_from_config(mock_get_tracker_class):
    """get_tracker should raise TypeError when tracker class lacks from_config()."""
    fake_tracker_cls = MagicMock()
    fake_tracker_cls.__name__ = "FakeTracker"
    # Ensure no from_config
    if hasattr(fake_tracker_cls, "from_config"):
        del fake_tracker_cls.from_config

    mock_get_tracker_class.return_value = fake_tracker_cls

    config = {
        "issue-tracker": {"name": "somekey"},
        "somekey": {"foo": "bar"},
    }

    with pytest.raises(TypeError) as excinfo:
        gibr.factory.get_tracker(config)

    assert "must implement from_config" in str(excinfo.value)
