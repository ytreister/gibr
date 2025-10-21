"""Tests for gibr.registry module."""

import pytest

from gibr import registry


def test_register_tracker_adds_entry():
    """register_tracker should add an entry to TRACKER_REGISTRY."""
    # Clear registry before test
    registry.TRACKER_REGISTRY.clear()

    @registry.register_tracker("dummy", "DummyTracker")
    class DummyTracker:
        pass

    assert "dummy" in registry.TRACKER_REGISTRY
    entry = registry.TRACKER_REGISTRY["dummy"]
    assert entry["class"] is DummyTracker
    assert entry["display_name"] == "DummyTracker"
    assert entry["supported"] is True


def test_register_tracker_can_mark_unsupported():
    """register_tracker should store supported=False when given."""
    registry.TRACKER_REGISTRY.clear()

    @registry.register_tracker("unsupported", "UnsupportedTracker", supported=False)
    class UnsupportedTracker:
        pass

    info = registry.TRACKER_REGISTRY["unsupported"]
    assert info["supported"] is False


def test_get_tracker_class_returns_registered_class():
    """get_tracker_class should return the correct tracker class."""
    registry.TRACKER_REGISTRY.clear()

    @registry.register_tracker("jira", "JIRATracker")
    class JiraTracker:
        pass

    result = registry.get_tracker_class("jira")
    assert result is JiraTracker


def test_get_tracker_class_raises_for_unknown_key():
    """get_tracker_class should raise ValueError for unknown tracker key."""
    registry.TRACKER_REGISTRY.clear()

    with pytest.raises(ValueError) as excinfo:
        registry.get_tracker_class("unknown")

    assert "Unsupported tracker type: unknown" in str(excinfo.value)
