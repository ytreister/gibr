"""Tests for the YouTrackTracker class."""

from unittest.mock import MagicMock, patch

import click
import pytest

from gibr.issue import Issue
from gibr.trackers.youtrack import YouTrackTracker


def make_response(
    fields=None,
    status=200,
    text="mocked response",
):
    """Create a mocked requests.Response object."""
    mock_resp = MagicMock()
    mock_resp.status_code = status
    if fields:
        items = [
            {
                "idReadable": field.get("idReadable"),
                "summary": field.get("summary"),
                "customFields": [
                    {
                        "value": {"name": field.get("issue_type")},
                        "name": "Type",
                    },
                    {
                        "value": {"login": field.get("assignee")},
                        "name": "Assignee",
                    },
                ],
            }
            for field in fields
        ]
        if len(items) == 1:
            mock_resp.json.return_value = items[0]
        else:
            mock_resp.json.return_value = items

    mock_resp.text = text
    return mock_resp


def test_from_config_creates_instance():
    """Test from_config creates YouTrackTracker instance correctly."""
    config = {"url": "https://yt", "token": "tok", "project": "PROJ"}
    tracker = YouTrackTracker.from_config(config)
    assert isinstance(tracker, YouTrackTracker)
    assert tracker.url == "https://yt"
    assert tracker.token == "tok"
    assert tracker.project == "PROJ"


@pytest.mark.parametrize("missing_key", ["url", "token"])
def test_from_config_raises_valueerror_for_missing_keys(missing_key):
    """Test from_config raises ValueError when required keys are missing."""
    base = {"url": "https://yt", "token": "tok", "project": "PROJ"}
    bad = base.copy()
    del bad[missing_key]
    with pytest.raises(ValueError) as excinfo:
        YouTrackTracker.from_config(bad)
    assert f"Missing key in 'youtrack' config: {missing_key}" in str(excinfo.value)


@patch(
    "gibr.trackers.youtrack.requests.get",
    return_value=make_response(
        fields=[
            {
                "idReadable": "PROJ-1",
                "summary": "Test issue",
                "assignee": "bob",
                "issue_type": "Bug",
            }
        ]
    ),
)
def test_get_issue_success(_):
    """Test get_issue returns Issue object on success."""
    tracker = YouTrackTracker(url="https://yt", token="tok")
    issue = tracker.get_issue("PROJ-1")
    assert isinstance(issue, Issue)
    assert issue.id == "PROJ-1"
    assert issue.title == "Test issue"
    assert issue.assignee == "bob"
    assert issue.type == "Bug"


@patch(
    "gibr.trackers.youtrack.requests.get",
    return_value=make_response(status=404, text="not found"),
)
@patch("gibr.trackers.youtrack.error", side_effect=click.Abort)
def test_get_issue_not_found(mock_error, _):
    """Test get_issue handles 404 Not Found error."""
    tracker = YouTrackTracker(url="https://yt", token="tok")
    with pytest.raises(click.Abort):
        tracker.get_issue("PROJ-999")
    mock_error.assert_called_once()
    assert "not found" in mock_error.call_args[0][0].lower()


@patch(
    "gibr.trackers.youtrack.requests.get",
    return_value=make_response(status=500, text="fail"),
)
@patch("gibr.trackers.youtrack.error", side_effect=click.Abort)
def test_get_issue_api_error(mock_error, _):
    """Test get_issue handles non-404 API errors."""
    tracker = YouTrackTracker(url="https://yt", token="tok")
    with pytest.raises(click.Abort):
        tracker.get_issue("PROJ-1")
    mock_error.assert_called_once()
    assert "api request failed" in mock_error.call_args[0][0].lower()


@patch(
    "gibr.trackers.youtrack.requests.get",
    return_value=make_response(
        fields=[
            {"idReadable": "PROJ-1", "summary": "A", "assignee": "bob"},
            {"idReadable": "PROJ-2", "summary": "B", "assignee": "alice"},
        ],
    ),
)
def test_list_issues_success(_):
    """Test list_issues returns a list of Issue objects on success."""
    tracker = YouTrackTracker(url="https://yt", token="tok", project="PROJ")
    issues = tracker.list_issues()
    assert isinstance(issues, list)
    expected_count = 2
    assert len(issues) == expected_count
    assert all(isinstance(i, Issue) for i in issues)
    assert issues[0].id == "PROJ-1"
    assert issues[1].assignee == "alice"


@patch(
    "gibr.trackers.youtrack.requests.get",
    return_value=make_response(status=500, text="fail"),
)
@patch("gibr.trackers.youtrack.error", side_effect=click.Abort)
def test_list_issues_api_error(mock_error, _):
    """Test list_issues handles API errors."""
    tracker = YouTrackTracker(url="https://yt", token="tok", project="PROJ")
    with pytest.raises(click.Abort):
        tracker.list_issues()
    mock_error.assert_called_once()
    assert "api request failed" in mock_error.call_args[0][0].lower()


def test_describe_config_returns_expected_format():
    """Test describe_config returns a formatted string with config details."""
    config = {"url": "https://yt", "project": "PROJ", "token": "tok"}
    result = YouTrackTracker.describe_config(config)
    assert result.startswith("YouTrack:")
    assert "URL" in result
    assert "Project" in result
    assert "Token" in result
    assert "https://yt" in result
    assert "PROJ" in result
    assert "tok" in result


@patch.object(YouTrackTracker, "check_token")
@patch(
    "click.prompt",
    side_effect=["https://yt", "PROJ", "YOUTRACK_TOKEN"],
)
def test_configure_interactively(mock_prompt, mock_check_token):
    """Test configure_interactively prompts user and returns config dict."""
    result = YouTrackTracker.configure_interactively()
    expected_count = 3
    assert mock_prompt.call_count == expected_count
    mock_check_token.assert_called_once_with("YOUTRACK_TOKEN")
    assert result == {
        "url": "https://yt",
        "project": "PROJ",
        "token": "${YOUTRACK_TOKEN}",
    }


@pytest.mark.parametrize(
    "method,field_name",
    [
        ("_get_custom_field_value", "Type"),
        ("_get_custom_field_value", "Assignee"),
        ("_get_assignee", None),
        ("_get_type", None),
    ],
)
def test_missing_fields_return_none(method, field_name):
    """Test that missing fields return None."""
    tracker = YouTrackTracker(url="https://yt", token="tok")
    issue = {"customFields": []}

    func = getattr(tracker, method)

    if field_name is None:
        assert func(issue) is None
    else:
        assert func(issue, field_name) is None


@patch("gibr.trackers.youtrack.error", side_effect=click.Abort)
def test_get_issue_numeric_without_project_calls_error(mock_error):
    """Numeric issue id without project should call error()."""
    tracker = YouTrackTracker(url="https://yt", token="tok", project=None)
    with pytest.raises(click.Abort):
        tracker.get_issue("123")
    mock_error.assert_called_once()
    assert "numeric issue id" in mock_error.call_args[0][0].lower()


@patch(
    "gibr.trackers.youtrack.requests.get",
    return_value=make_response(
        fields=[
            {
                "idReadable": "PROJ-123",
                "summary": "Num issue",
                "assignee": "dave",
                "issue_type": "Task",
            }
        ]
    ),
)
def test_get_issue_numeric_with_project_success(_):
    """Numeric issue id should expand to PROJECT-id and succeed."""
    tracker = YouTrackTracker(url="https://yt", token="tok", project="PROJ")
    issue = tracker.get_issue("123")
    assert issue.id == "PROJ-123"
    assert issue.title == "Num issue"
    assert issue.assignee == "dave"
    assert issue.type == "Task"
