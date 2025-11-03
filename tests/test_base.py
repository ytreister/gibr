"""Tests for IssueTracker base class."""

import os
from unittest.mock import patch

from gibr.trackers.base import IssueTracker


class DummyTracker(IssueTracker):
    """Dummy tracker for testing."""

    display_name = "Dummy"


@patch("gibr.trackers.base.party")
@patch.dict(os.environ, {"DUMMY_TOKEN": "abc123"})
def test_check_token_found(mock_party):
    """Should call party() when token is found in env."""
    DummyTracker.check_token("DUMMY_TOKEN")
    mock_party.assert_called_once()
    assert "Dummy token in environment" in mock_party.call_args[0][0]


@patch("gibr.trackers.base.warning")
@patch.dict(os.environ, {}, clear=True)
def test_check_token_missing(mock_warning, capsys):
    """Should warn and print export instructions when token missing."""
    DummyTracker.check_token("DUMMY_TOKEN")

    mock_warning.assert_called_once()
    out = capsys.readouterr().out
    assert "export DUMMY_TOKEN" in out
    assert "setx DUMMY_TOKEN" in out


@patch("gibr.trackers.base.error")
def test_import_error_message(mock_error):
    """Should show proper error message and install commands."""
    DummyTracker.import_error("python-gitlab", "gitlab")

    mock_error.assert_called_once()
    msg = mock_error.call_args[0][0]

    # Check key parts of message
    assert "python-gitlab not installed." in msg
    assert "Install optional dependency with:" in msg
    assert "pip install gibr[gitlab]" in msg
    assert "uv pip install gibr[gitlab]" in msg
