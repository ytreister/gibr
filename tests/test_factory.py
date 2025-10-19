"""Tests for the factory."""

from unittest.mock import patch

import pytest

from gibr.trackers.factory import get_tracker


@patch("gibr.trackers.factory.GithubTracker")
def test_get_tracker_github(mock_github_tracker):
    """Test that get_tracker returns correct tracker for github."""
    config = {
        "issue-tracker": {"name": "github"},
        "github": {"repo": "user/repo", "token": "abc123"},
    }

    tracker_instance = mock_github_tracker.return_value
    result = get_tracker(config)
    mock_github_tracker.assert_called_once_with(repo="user/repo", token="abc123")
    assert result == tracker_instance


def test_get_tracker_unsupported_type():
    """Test that get_tracker raises ValueError for unsupported tracker types."""
    config = {"issue-tracker": {"name": "jira"}}

    with pytest.raises(ValueError, match="Unsupported tracker type: jira"):
        get_tracker(config)


@pytest.mark.parametrize(
    "config,expected_msg",
    [
        ({}, "Missing 'issue-tracker.name' in config"),
        ({"issue-tracker": {}}, "Missing 'issue-tracker.name' in config"),
        (
            {"issue-tracker": {"name": "github"}},
            "Missing 'github' config",
        ),
        (
            {"issue-tracker": {"name": "github"}, "github": {"repo": "user/repo"}},
            "Missing key in 'github' config: token",
        ),
        (
            {"issue-tracker": {"name": "github"}, "github": {"token": "abc123"}},
            "Missing key in 'github' config: repo",
        ),
    ],
)
def test_get_tracker_invalid_config(config, expected_msg):
    """Test that get_tracker raises proper ValueError for invalid configs."""
    with pytest.raises(ValueError, match=expected_msg):
        get_tracker(config)
