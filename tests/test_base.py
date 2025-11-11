"""Tests for IssueTracker base class."""

import os
from http import HTTPStatus
from unittest.mock import MagicMock, patch

import click
import pytest

from gibr.trackers.base import IssueTracker


class DummyTracker(IssueTracker):
    """Dummy tracker for testing."""

    token = "token"
    display_name = "Dummy"
    API_URL = "api.com/"

    def list_issues(self):
        """Stub."""

    def get_issue(self):
        """Stub."""

    def _get_assignee(self):
        """Stub."""


def make_response(status=HTTPStatus.OK, json_data=None):
    """Create a mock response object."""
    mock_resp = MagicMock()
    mock_resp.status_code = status
    mock_resp.json.return_value = json_data or {}
    mock_resp.text = "mocked response"
    return mock_resp


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
    assert "uv tool install --with gitlab gibr" in msg


@patch("gibr.trackers.base.error", side_effect=click.Abort)
@patch("gibr.trackers.base.requests.post")
def test_graphql_request_non_200_triggers_error(mock_post, mock_error):
    """_graphql_request should call error() if status != 200."""
    tracker = DummyTracker()
    mock_post.return_value = make_response(status=HTTPStatus.BAD_REQUEST)

    with pytest.raises(click.Abort):
        tracker._graphql_request("query")

    mock_error.assert_called_once()
    assert "Dummy API request failed" in mock_error.call_args[0][0]


@patch("gibr.trackers.base.error", side_effect=click.Abort)
@patch("gibr.trackers.base.requests.post")
def test_graphql_request_handles_graphql_errors(mock_post, mock_error):
    """_graphql_request should call error() if response contains GraphQL 'errors'."""
    tracker = DummyTracker()

    mock_post.return_value = MagicMock(
        status_code=HTTPStatus.OK,
        json=lambda: {"errors": [{"message": "Some GraphQL failure"}]},
        text="mocked text",
    )

    with pytest.raises(click.Abort):
        tracker._graphql_request("query { something }")

    mock_error.assert_called_once()
    assert "Some GraphQL failure" in str(mock_error.call_args[0][0])
