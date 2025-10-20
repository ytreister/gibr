"""Tests for the JiraTracker class."""

from unittest.mock import MagicMock, patch

import click
import pytest
from jira import JIRAError

from gibr.issue import Issue
from gibr.trackers.jira import JiraTracker


@pytest.fixture
def mock_jira_client():
    """Fixture returning a mock JIRA client with a fake issue."""
    client = MagicMock()

    mock_issue = MagicMock()
    mock_issue.key = "PROJ-123"
    mock_issue.fields = MagicMock()
    mock_issue.fields.summary = "Implement feature X"
    mock_issue.fields.issuetype = MagicMock()
    mock_issue.fields.issuetype.name = "Task"

    client.issue.return_value = mock_issue
    client.search_issues.return_value = [mock_issue]
    return client


@patch("gibr.trackers.jira.JIRA")
def test_init_success(mock_jira_cls, mock_jira_client):
    """JiraTracker initializes and stores client and project key."""
    mock_jira_cls.return_value = mock_jira_client

    tracker = JiraTracker(url="http://jira", user="u", token="t", project_key="PROJ")

    assert tracker.client is mock_jira_client
    assert tracker.project_key == "PROJ"


@patch("gibr.trackers.jira.JIRA")
def test_get_issue_success(mock_jira_cls, mock_jira_client):
    """get_issue should return an Issue with correct fields on success."""
    mock_jira_cls.return_value = mock_jira_client

    tracker = JiraTracker(url="http://jira", user="u", token="t", project_key="PROJ")
    issue = tracker.get_issue("123")

    mock_jira_client.issue.assert_called_once_with("PROJ-123")
    assert isinstance(issue, Issue)
    assert issue.id == "PROJ-123"
    assert issue.title == "Implement feature X"
    assert issue.type == "Task"


@patch("gibr.trackers.jira.error")
@patch("gibr.trackers.jira.JIRA")
def test_get_issue_not_found(mock_jira_cls, mock_error):
    """Test issue not found handling in get_issue."""
    mock_error.side_effect = click.Abort
    mock_client = mock_jira_cls.return_value
    mock_client.issue.side_effect = JIRAError(status_code=404, text="not found")

    tracker = JiraTracker(url="http://jira", user="u", token="t", project_key="PROJ")

    with pytest.raises(click.Abort):
        tracker.get_issue("999")

    mock_error.assert_called_once_with("Issue PROJ-999 not found in Jira project PROJ.")


@patch("gibr.trackers.jira.JIRA")
def test_list_issues_returns_list(mock_jira_cls, mock_jira_client):
    """list_issues should return a list of Issue objects."""
    mock_jira_cls.return_value = mock_jira_client

    tracker = JiraTracker(url="http://jira", user="u", token="t", project_key="PROJ")
    issues = tracker.list_issues()

    mock_jira_client.search_issues.assert_called_once()
    assert isinstance(issues, list)
    assert len(issues) == 1
    assert isinstance(issues[0], Issue)
    assert issues[0].title == "Implement feature X"


@patch("gibr.trackers.jira.JIRA")
def test_init_raises_valueerror_on_connection_failure(mock_jira_cls):
    """If the JIRA constructor raises JIRAError, JiraTracker should raise ValueError."""
    mock_jira_cls.side_effect = JIRAError(text="auth failed")

    with pytest.raises(ValueError) as e:
        JiraTracker(url="http://jira", user="u", token="t", project_key="PROJ")

    assert "Failed to connect to Jira" in str(e.value)
