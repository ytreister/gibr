"""Tests for the GithubTracker class."""

from unittest.mock import MagicMock, patch

import click
import pytest
from github.GithubException import UnknownObjectException

from gibr.issue import Issue
from gibr.trackers.github import GithubTracker


@pytest.fixture
def mock_github_repo():
    """Fixture returning a mock repo with fake issues."""
    mock_repo = MagicMock()
    mock_issue = MagicMock(number=123, title="Fix login bug")
    mock_repo.get_issue.return_value = mock_issue
    mock_repo.get_issues.return_value = [mock_issue]
    return mock_repo


@pytest.fixture
def mock_github_client(mock_github_repo):
    """Fixture returning a mock Github client."""
    mock_client = MagicMock()
    mock_client.get_repo.return_value = mock_github_repo
    return mock_client


@patch("gibr.trackers.github.Github")
def test_get_issue_success(mock_github_cls, mock_github_client, mock_github_repo):
    """Test successful get_issue returns Issue object with correct fields."""
    issue_number = 123
    mock_github_cls.return_value = mock_github_client

    tracker = GithubTracker(repo="owner/repo", token="fake-token")
    issue = tracker.get_issue(str(issue_number))

    mock_github_repo.get_issue.assert_called_once_with(number=issue_number)
    assert isinstance(issue, Issue)
    assert issue.id == issue_number
    assert issue.title == "Fix login bug"
    assert issue.type == "issue"


@patch("gibr.trackers.github.error")
@patch("gibr.trackers.github.Github")
def test_get_issue_not_found(mock_github_cls, mock_error):
    """Test that click.Abort is raised when issue is not found."""
    mock_error.side_effect = click.Abort

    mock_repo = mock_github_cls.return_value.get_repo.return_value
    mock_repo.get_issue.side_effect = UnknownObjectException(404, "Not Found", None)

    tracker = GithubTracker(repo="owner/repo", token="fake-token")

    with pytest.raises(click.Abort):
        tracker.get_issue("999")
    mock_error.assert_called_once_with("Issue #999 not found in repository.")


@patch("gibr.trackers.github.Github")
def test_list_issues_returns_list(
    mock_github_cls, mock_github_client, mock_github_repo
):
    """Test list_issues returns list of Issue objects."""
    mock_github_cls.return_value = mock_github_client

    tracker = GithubTracker(repo="owner/repo", token="fake-token")
    issues = tracker.list_issues()

    mock_github_repo.get_issues.assert_called_once_with(state="open")
    assert isinstance(issues, list)
    assert len(issues) == 1
    assert isinstance(issues[0], Issue)
    assert issues[0].title == "Fix login bug"
