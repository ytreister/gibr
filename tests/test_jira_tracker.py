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
def test_from_config_creates_instance(mock_jira_cls, mock_jira_client):
    """from_config should create JiraTracker with correct params."""
    mock_jira_cls.return_value = mock_jira_client

    config = {
        "url": "http://jira",
        "user": "me",
        "token": "secret",
        "project_key": "PROJ",
    }

    tracker = JiraTracker.from_config(config)

    mock_jira_cls.assert_called_once_with(
        server="http://jira", basic_auth=("me", "secret")
    )
    assert isinstance(tracker, JiraTracker)
    assert tracker.project_key == "PROJ"
    assert tracker.client is mock_jira_client


@pytest.mark.parametrize("missing_key", ["url", "user", "token"])
def test_from_config_raises_valueerror_for_missing_keys(missing_key):
    """from_config should raise ValueError for each missing required key."""
    base_config = {
        "url": "http://jira",
        "user": "me",
        "token": "secret",
        "project_key": "PROJ",
    }
    bad_config = base_config.copy()
    del bad_config[missing_key]

    with pytest.raises(ValueError) as excinfo:
        JiraTracker.from_config(bad_config)

    assert f"Missing key in 'jira' config: {missing_key}" in str(excinfo.value)


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
def test_get_issue_not_found_with_project(mock_jira_cls, mock_error):
    """If project_key is set, show project-specific error message."""
    mock_error.side_effect = click.Abort
    mock_client = mock_jira_cls.return_value
    mock_client.issue.side_effect = JIRAError(status_code=404, text="not found")

    tracker = JiraTracker(url="http://jira", user="u", token="t", project_key="PROJ")

    with pytest.raises(click.Abort):
        tracker.get_issue("999")

    mock_error.assert_called_once_with("Issue PROJ-999 not found in Jira project PROJ.")


@patch("gibr.trackers.jira.error")
@patch("gibr.trackers.jira.JIRA")
def test_get_issue_not_found_without_project(mock_jira_cls, mock_error):
    """If no project_key is set, show instance-wide error message."""
    mock_error.side_effect = click.Abort
    mock_client = mock_jira_cls.return_value
    mock_client.issue.side_effect = JIRAError(status_code=404, text="not found")

    tracker = JiraTracker(url="http://jira", user="u", token="t")

    with pytest.raises(click.Abort):
        tracker.get_issue("PROJ-999")

    mock_error.assert_called_once_with("Issue PROJ-999 not found in Jira instance.")


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
def test_init_success(mock_jira_cls, mock_jira_client):
    """JiraTracker initializes and stores client and project key."""
    mock_jira_cls.return_value = mock_jira_client

    tracker = JiraTracker(url="http://jira", user="u", token="t", project_key="PROJ")

    assert tracker.client is mock_jira_client
    assert tracker.project_key == "PROJ"


@patch("gibr.trackers.jira.JIRA")
def test_init_raises_valueerror_on_connection_failure(mock_jira_cls):
    """If the JIRA constructor raises JIRAError, JiraTracker should raise ValueError."""
    mock_jira_cls.side_effect = JIRAError(text="auth failed")

    with pytest.raises(ValueError) as e:
        JiraTracker(url="http://jira", user="u", token="t", project_key="PROJ")

    assert "Failed to connect to Jira" in str(e.value)


def test_describe_config_returns_expected_format():
    """describe_config() should return a formatted summary of the config."""
    config = {
        "url": "https://example.atlassian.net",
        "project_key": "TEST",
        "user": "alice",
        "token": "abc123",
    }

    result = JiraTracker.describe_config(config)

    # Core structure
    assert result.startswith("Jira:")
    assert "URL" in result
    assert "Project Key" in result
    assert "User" in result
    assert "Token" in result

    # Values interpolated correctly
    assert "https://example.atlassian.net" in result
    assert "TEST" in result
    assert "alice" in result
    assert "abc123" in result


@patch.object(JiraTracker, "check_token")
@patch(
    "click.prompt",
    side_effect=[
        "https://company.atlassian.net",
        "PROJ",
        "me@company.com",
        "MY_JIRA_TOKEN",
    ],
)
def test_configure_interactively(mock_prompt, mock_check_token):
    """Should prompt user for Jira settings and return correct dict."""
    result = JiraTracker.configure_interactively()
    expected_call_count = 4
    assert mock_prompt.call_count == expected_call_count
    mock_check_token.assert_called_once_with("MY_JIRA_TOKEN")

    # Verify the returned config
    assert result == {
        "url": "https://company.atlassian.net",
        "project_key": "PROJ",
        "user": "me@company.com",
        "token": "${MY_JIRA_TOKEN}",
    }


@pytest.mark.parametrize(
    "issue,expected",
    [
        ("FOO-123", True),
        ("ABC_DEF-999", True),
        ("FOO-0", True),
        (" FOO-123 ", True),  # leading/trailing whitespace handled
        ("FOO123", False),  # missing dash
        ("FOO-", False),  # missing number
        ("-123", False),  # missing prefix
        ("foo-123", False),  # lowercase prefix invalid
        ("FOO-ABC", False),  # numeric part must be digits
        ("", False),
        ("123-FOO", False),
        ("Fii-FOO", False),  # first is uppercase, followed by lowercase
    ],
)
def test_is_jira_issue(issue, expected):
    """is_jira_issue should correctly validate Jira issue keys."""
    assert JiraTracker.is_jira_issue(issue) is expected


@pytest.mark.parametrize(
    "key,expected",
    [
        ("PROJ", True),
        ("ABC_DEF", True),
        ("ABC_DEF_123", True),  # valid with mix of alpnanumeric and numbers
        (" ABC_DEF_123 ", True),  # leading/trailing whitespace handled
        ("A1B2", True),
        ("_PROJ", False),  # must start with a letter
        ("proj", False),  # lowercase invalid
        ("123", False),  # must start with a letter
        ("A-B", False),  # dash not allowed
        ("", False),
        ("A B", False),  # spaces not allowed
    ],
)
def test_is_jira_project_key(key, expected):
    """is_jira_project_key should correctly validate Jira project keys."""
    assert JiraTracker.is_jira_project_key(key) is expected
