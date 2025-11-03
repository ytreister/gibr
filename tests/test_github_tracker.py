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
    mock_issue = MagicMock(number=123, title="Fix login bug", pull_request=None)
    mock_repo.get_issue.return_value = mock_issue
    mock_repo.get_issues.return_value = [mock_issue]
    return mock_repo


@pytest.fixture
def mock_github_client(mock_github_repo):
    """Fixture returning a mock Github client."""
    mock_client = MagicMock()
    mock_client.get_repo.return_value = mock_github_repo
    return mock_client


@patch("gibr.trackers.github.error")
@patch("github.Github")
def test_init_repo_not_found(mock_github_cls, mock_error):
    """GithubTracker.__init__ should call error() when repo is not found."""
    mock_client = MagicMock()
    mock_client.get_repo.side_effect = UnknownObjectException(404, "Not Found", None)
    mock_github_cls.return_value = mock_client
    mock_error.side_effect = click.Abort  # to simulate the behavior of error()

    with pytest.raises(click.Abort):
        GithubTracker(repo="invalid/repo", token="fake-token")

    mock_error.assert_called_once_with(
        "The specified repo could not be found: invalid/repo"
    )


@patch("github.Github")
@patch("github.Auth")
def test_from_config_creates_instance(mock_auth, mock_github):
    """from_config should create GithubTracker with correct params."""
    mock_client = MagicMock()
    mock_repo = MagicMock()
    mock_github.return_value = mock_client
    mock_client.get_repo.return_value = mock_repo

    config = {"repo": "owner/repo", "token": "secrettoken"}

    tracker = GithubTracker.from_config(config)

    mock_auth.Token.assert_called_once_with("secrettoken")
    mock_github.assert_called_once_with(auth=mock_auth.Token.return_value)
    mock_client.get_repo.assert_called_once_with("owner/repo")
    assert isinstance(tracker, GithubTracker)
    assert tracker.repo is mock_repo


@pytest.mark.parametrize("missing_key", ["repo", "token"])
def test_from_config_raises_valueerror_for_missing_keys(missing_key):
    """from_config should raise ValueError for each missing required key."""
    base_config = {"repo": "owner/repo", "token": "secrettoken"}
    bad_config = base_config.copy()
    del bad_config[missing_key]

    with pytest.raises(ValueError) as excinfo:
        GithubTracker.from_config(bad_config)

    assert f"Missing key in 'github' config: {missing_key}" in str(excinfo.value)


@patch("github.Github")
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
@patch("github.Github")
def test_get_issue_not_found(mock_github_cls, mock_error):
    """Test that click.Abort is raised when issue is not found."""
    mock_error.side_effect = click.Abort

    mock_repo = mock_github_cls.return_value.get_repo.return_value
    mock_repo.get_issue.side_effect = UnknownObjectException(404, "Not Found", None)

    tracker = GithubTracker(repo="owner/repo", token="fake-token")

    with pytest.raises(click.Abort):
        tracker.get_issue("999")
    mock_error.assert_called_once_with("Issue #999 not found in repository.")


@patch("github.Github")
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


@patch("github.Github")
def test_list_issues_excludes_pull_requests(
    mock_github_cls, mock_github_client, mock_github_repo
):
    """list_issues should exclude pull requests from the returned list."""
    # Mock one issue and one pull request
    mock_issue = MagicMock(number=1, title="Real issue", pull_request=None)
    mock_pr = MagicMock(
        number=2, title="PR: not an issue", pull_request={"url": "https://..."}
    )
    mock_github_repo.get_issues.return_value = [mock_issue, mock_pr]

    mock_github_cls.return_value = mock_github_client

    tracker = GithubTracker(repo="owner/repo", token="fake-token")
    issues = tracker.list_issues()

    mock_github_repo.get_issues.assert_called_once_with(state="open")

    # Only the real issue should be returned
    assert len(issues) == 1
    assert issues[0].id == 1
    assert issues[0].title == "Real issue"
    assert issues[0].type == "issue"


def test_describe_config_returns_expected_format():
    """describe_config() should return a formatted summary of the config."""
    config = {"repo": "owner/repo", "token": "secrettoken"}

    result = GithubTracker.describe_config(config)

    # Core structure
    assert result.startswith("Github:")
    assert "Repo" in result
    assert "Token" in result

    # Values interpolated correctly
    assert "owner/repo" in result
    assert "secrettoken" in result


@patch.object(GithubTracker, "check_token")
@patch("click.prompt", side_effect=["user/repo", "MY_GITHUB_TOKEN"])
def test_github_configure_interactively(mock_prompt, mock_check_token):
    """Should prompt user for GitHub settings and return correct dict."""
    result = GithubTracker.configure_interactively()
    expected_call_count = 2
    assert mock_prompt.call_count == expected_call_count
    mock_check_token.assert_called_once_with("MY_GITHUB_TOKEN")

    # Verify result dictionary
    assert result == {
        "repo": "user/repo",
        "token": "${MY_GITHUB_TOKEN}",
    }


@patch.object(GithubTracker, "import_error", side_effect=SystemExit)
def test_import_error_called_when_github_missing(mock_import_error):
    """Should call import_error() when python-gitlab is not installed."""
    with patch("builtins.__import__", side_effect=ImportError):
        with pytest.raises(SystemExit):
            GithubTracker(repo="user/repo", token="tok")

    mock_import_error.assert_called_once_with("PyGithub", "github")
