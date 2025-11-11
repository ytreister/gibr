"""Tests for the GitlabTracker class."""

from unittest.mock import MagicMock, patch

import click
import pytest
from gitlab.exceptions import GitlabGetError

from gibr.issue import Issue
from gibr.trackers.gitlab import GitlabTracker


@pytest.fixture
def mock_gitlab_project():
    """Fixture returning a mock GitLab project with fake issues."""
    mock_project = MagicMock()
    mock_issue = MagicMock(iid=42, title="Fix pipeline bug")
    mock_project.issues.get.return_value = mock_issue
    mock_project.issues.list.return_value = [mock_issue]
    return mock_project


@pytest.fixture
def mock_gitlab_client(mock_gitlab_project):
    """Fixture returning a mock GitLab client."""
    mock_client = MagicMock()
    mock_client.projects.get.return_value = mock_gitlab_project
    return mock_client


@patch("gitlab.Gitlab")
def test_from_config_creates_instance(
    mock_gitlab_cls, mock_gitlab_client, mock_gitlab_project
):
    """from_config should create GitlabTracker with correct params."""
    mock_gitlab_cls.return_value = mock_gitlab_client
    config = {
        "url": "https://gitlab.com",
        "token": "secrettoken",
        "project": "group/proj",
    }
    tracker = GitlabTracker.from_config(config)
    mock_gitlab_cls.assert_called_once_with(
        "https://gitlab.com", private_token="secrettoken"
    )
    mock_gitlab_client.projects.get.assert_called_once_with("group/proj")
    assert isinstance(tracker, GitlabTracker)
    assert tracker.project is mock_gitlab_project


@pytest.mark.parametrize("missing_key", ["url", "token", "project"])
def test_from_config_raises_valueerror_for_missing_keys(missing_key):
    """from_config should raise ValueError for each missing required key."""
    base_config = {
        "url": "https://gitlab.com",
        "token": "secrettoken",
        "project": "group/proj",
    }
    bad_config = base_config.copy()
    del bad_config[missing_key]
    with pytest.raises(ValueError) as excinfo:
        GitlabTracker.from_config(bad_config)
    assert f"Missing key in 'gitlab' config: {missing_key}" in str(excinfo.value)


@patch("gitlab.Gitlab")
def test_get_issue_success(mock_gitlab_cls, mock_gitlab_client, mock_gitlab_project):
    """Test successful get_issue returns Issue object with correct fields."""
    mock_gitlab_cls.return_value = mock_gitlab_client
    tracker = GitlabTracker(url="https://gitlab.com", token="tok", project="group/proj")
    issue = tracker.get_issue("42")
    mock_gitlab_project.issues.get.assert_called_once_with("42")
    assert isinstance(issue, Issue)
    issue_id = 42
    assert issue.id == issue_id
    assert issue.title == "Fix pipeline bug"
    assert issue.type == "issue"


@patch("gibr.trackers.gitlab.error")
@patch("gitlab.Gitlab")
def test_get_issue_not_found(
    mock_gitlab_cls, mock_error, mock_gitlab_client, mock_gitlab_project
):
    """Test that click.Abort is raised when issue is not found."""
    mock_error.side_effect = click.Abort
    mock_gitlab_cls.return_value = mock_gitlab_client
    mock_gitlab_project.issues.get.side_effect = GitlabGetError(404, "Not Found")
    tracker = GitlabTracker(url="https://gitlab.com", token="tok", project="group/proj")
    with pytest.raises(click.Abort):
        tracker.get_issue("999")
    mock_error.assert_called_once_with(
        "Issue #999 not found in GitLab project group/proj."
    )


@patch("gitlab.Gitlab")
def test_list_issues_returns_list(
    mock_gitlab_cls, mock_gitlab_client, mock_gitlab_project
):
    """Test list_issues returns list of Issue objects."""
    mock_gitlab_cls.return_value = mock_gitlab_client
    tracker = GitlabTracker(url="https://gitlab.com", token="tok", project="group/proj")
    issues = tracker.list_issues()
    mock_gitlab_project.issues.list.assert_called_once_with(state="opened", all=True)
    assert isinstance(issues, list)
    assert len(issues) == 1
    assert isinstance(issues[0], Issue)
    assert issues[0].title == "Fix pipeline bug"
    assert issues[0].type == "issue"


def test_describe_config_returns_expected_format():
    """describe_config() should return a formatted summary of the config."""
    config = {"url": "https://gitlab.com", "project": "group/proj", "token": "tok"}
    result = GitlabTracker.describe_config(config)
    assert result.startswith("GitLab:")
    assert "URL" in result
    assert "Project" in result
    assert "Token" in result
    assert "https://gitlab.com" in result
    assert "group/proj" in result
    assert "tok" in result


@patch.object(GitlabTracker, "check_token")
@patch(
    "click.prompt", side_effect=["https://gitlab.com", "group/proj", "MY_GITLAB_TOKEN"]
)
def test_gitlab_configure_interactively(mock_prompt, mock_check_token):
    """Should prompt user for GitLab settings and return correct dict."""
    result = GitlabTracker.configure_interactively()
    expected_call_count = 3
    assert mock_prompt.call_count == expected_call_count
    mock_check_token.assert_called_once_with("MY_GITLAB_TOKEN")
    assert result == {
        "url": "https://gitlab.com",
        "project": "group/proj",
        "token": "${MY_GITLAB_TOKEN}",
    }


@patch("gitlab.Gitlab")
def test_get_assignee_multiple_assignees(mock_gitlab_cls, mock_gitlab_client):
    """_get_assignee should return first username from multiple assignees."""
    mock_gitlab_cls.return_value = mock_gitlab_client
    tracker = GitlabTracker(url="https://gitlab.com", token="tok", project="group/proj")

    mock_issue = MagicMock()
    mock_issue.assignees = [{"username": "alice"}, {"username": "bob"}]
    result = tracker._get_assignee(mock_issue)
    assert result == "alice"


@patch("gitlab.Gitlab")
def test_get_assignee_no_assignees(mock_gitlab_cls, mock_gitlab_client):
    """_get_assignee should return None when no assignee info exists."""
    mock_gitlab_cls.return_value = mock_gitlab_client
    tracker = GitlabTracker(url="https://gitlab.com", token="tok", project="group/proj")

    mock_issue = MagicMock()
    mock_issue.assignees = None
    mock_issue.assignee = None
    result = tracker._get_assignee(mock_issue)
    assert result is None


@patch.object(GitlabTracker, "import_error", side_effect=SystemExit)
def test_import_error_called_when_gitlab_missing(mock_import_error):
    """Should call import_error() when python-gitlab is not installed."""
    with patch("builtins.__import__", side_effect=ImportError):
        with pytest.raises(SystemExit):
            GitlabTracker(url="https://gitlab.com", token="tok", project="group/proj")

    mock_import_error.assert_called_once_with("python-gitlab", "gitlab")
