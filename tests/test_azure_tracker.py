"""Tests for the AzureDevOpsTracker class."""

from unittest.mock import MagicMock, patch

import click
import pytest
from azure.devops.exceptions import AzureDevOpsClientError

from gibr.issue import Issue
from gibr.trackers.azure import AzureTracker


@pytest.fixture
def mock_work_item():
    """Fixture returning a mock Azure work item."""
    mock_item = MagicMock()
    mock_item.id = 42
    mock_item.fields = {
        "System.Title": "Fix pipeline bug",
        "System.WorkItemType": "Bug",
        "System.AssignedTo": {"displayName": "John Doe"},
    }
    return mock_item


@pytest.fixture
def mock_wit_client(mock_work_item):
    """Fixture returning a mock Work Item Tracking client."""
    mock_client = MagicMock()
    mock_client.get_work_item.return_value = mock_work_item
    mock_wiql_result = MagicMock()
    mock_wiql_result.work_items = [MagicMock(id=42)]
    mock_client.query_by_wiql.return_value = mock_wiql_result

    return mock_client


@pytest.fixture
def mock_connection(mock_wit_client):
    """Fixture returning a mock Azure DevOps connection."""
    mock_conn = MagicMock()
    mock_conn.clients.get_work_item_tracking_client.return_value = mock_wit_client
    return mock_conn


@patch("azure.devops.connection.Connection")
@patch("msrest.authentication.BasicAuthentication")
def test_from_config_creates_instance(
    mock_basic_auth, mock_connection, mock_wit_client
):
    """from_config should create AzureTracker with correct params."""
    # Setup the mock connection to return our mock WIT client
    mock_conn_instance = MagicMock()
    mock_conn_instance.clients.get_work_item_tracking_client.return_value = (
        mock_wit_client
    )
    mock_connection.return_value = mock_conn_instance

    # Setup BasicAuthentication mock
    mock_auth_instance = MagicMock()
    mock_basic_auth.return_value = mock_auth_instance

    config = {
        "url": "https://dev.azure.com/myorg",
        "token": "secrettoken",
        "project": "MyProject",
        "team": "MyTeam",
    }

    tracker = AzureTracker.from_config(config)

    # Verify BasicAuthentication was called correctly
    mock_basic_auth.assert_called_once_with("", "secrettoken")

    # Verify Connection was called correctly
    mock_connection.assert_called_once_with(
        base_url="https://dev.azure.com/myorg", creds=mock_auth_instance
    )

    # Verify the tracker was created correctly
    assert isinstance(tracker, AzureTracker)
    assert tracker.url == "https://dev.azure.com/myorg"
    assert tracker.project_name == "MyProject"
    assert tracker.team_name == "MyTeam"
    assert tracker.wit_client == mock_wit_client


@pytest.mark.parametrize("missing_key", ["url", "token", "project", "team"])
def test_from_config_raises_valueerror_for_missing_keys(missing_key):
    """from_config should raise ValueError for each missing required key."""
    base_config = {
        "url": "https://dev.azure.com/myorg",
        "token": "secrettoken",
        "project": "MyProject",
        "team": "MyTeam",
    }
    bad_config = base_config.copy()
    del bad_config[missing_key]
    with pytest.raises(ValueError) as excinfo:
        AzureTracker.from_config(bad_config)
    assert f"Missing key in 'azure' config: {missing_key}" in str(excinfo.value)


@patch("azure.devops.connection.Connection")
@patch("msrest.authentication.BasicAuthentication")
def test_get_issue_success(mock_azure_cls, mock_connection, mock_wit_client):
    """Test successful get_issue returns Issue object with correct fields."""
    # Setup mocks
    mock_conn_instance = MagicMock()
    mock_conn_instance.clients.get_work_item_tracking_client.return_value = (
        mock_wit_client
    )
    mock_connection.return_value = mock_conn_instance

    config = {
        "url": "https://dev.azure.com/myorg",
        "token": "secrettoken",
        "project": "MyProject",
        "team": "MyTeam",
    }

    tracker = AzureTracker.from_config(config)
    issue = tracker.get_issue("42")

    # Verify the WIT client was called correctly
    mock_wit_client.get_work_item.assert_called_once_with(42)

    # Verify the issue was formatted correctly
    assert isinstance(issue, Issue)
    issue_id = 42
    assert issue.id == issue_id
    assert issue.title == "Fix pipeline bug"
    assert issue.type == "Bug"
    assert issue.assignee == "John Doe"


@patch("gibr.trackers.azure.error")
@patch("azure.devops.connection.Connection")
@patch("msrest.authentication.BasicAuthentication")
def test_get_issue_not_found(
    mock_auth, mock_connection_cls, mock_error, mock_connection, mock_wit_client
):
    """Test that click.Abort is raised when issue is not found."""
    mock_error.side_effect = click.Abort
    mock_connection_cls.return_value = mock_connection
    mock_wit_client.get_work_item.side_effect = AzureDevOpsClientError("Not Found")
    tracker = AzureTracker(
        url="https://dev.azure.com/myorg",
        token="secrettoken",
        project="MyProject",
        team="MyTeam",
    )

    with pytest.raises(click.Abort):
        tracker.get_issue("999")

    mock_error.assert_called_once_with(
        "Issue #999 not found in Azure in the MyProject project for team MyTeam."
    )


@patch("azure.devops.connection.Connection")
@patch("msrest.authentication.BasicAuthentication")
def test_list_issues_returns_list(
    mock_auth, mock_connection_cls, mock_connection, mock_wit_client, mock_work_item
):
    """Test list_issues returns list of Issue objects."""
    mock_connection_cls.return_value = mock_connection
    tracker = AzureTracker(
        url="https://dev.azure.com/myorg ",
        token="secrettoken",
        project="proj",
        team="team",
    )
    issues = tracker.list_issues()

    mock_wit_client.query_by_wiql.assert_called_once()
    assert isinstance(issues, list)
    assert len(issues) == 1
    assert isinstance(issues[0], Issue)
    assert issues[0].title == "Fix pipeline bug"
    assert issues[0].type == "Bug"


def test_describe_config_returns_expected_format():
    """describe_config() should return a formatted summary of the config."""
    config = {
        "url": "https://dev.azure.com/myorg ",
        "project": "MyProject",
        "team": "MyTeam",
        "token": "secrettoken",
    }
    result = AzureTracker.describe_config(config)
    assert result.startswith("Azure DevOps:")
    assert "URL" in result
    assert "Project" in result
    assert "Team" in result
    assert "Token" in result
    assert "https://dev.azure.com/myorg" in result
    assert "MyProject" in result
    assert "MyTeam" in result
    assert "secrettoken" in result


@patch.object(AzureTracker, "check_token")
@patch(
    "click.prompt",
    side_effect=["https://dev.azure.com/myorg", "MyProject", "MyTeam", "AZURE_TOKEN"],
)
def test_azure_configure_interactively(mock_prompt, mock_check_token):
    """Should prompt user for Azure settings and return correct dict."""
    result = AzureTracker.configure_interactively()
    expected_call_count = 4
    assert mock_prompt.call_count == expected_call_count
    mock_check_token.assert_called_once_with("AZURE_TOKEN")
    assert result == {
        "url": "https://dev.azure.com/myorg",
        "project": "MyProject",
        "team": "MyTeam",
        "token": "${AZURE_TOKEN}",
    }


@patch("azure.devops.connection.Connection")
@patch("msrest.authentication.BasicAuthentication")
def test_get_assignee_with_assignee(mock_auth, mock_connection_cls, mock_connection):
    """_get_assignee should return displayName when assignee exists."""
    mock_connection_cls.return_value = mock_connection
    tracker = AzureTracker(
        url="https://dev.azure.com/myorg",
        token="secrettoken",
        project="MyProject",
        team="MyTeam",
    )
    mock_issue = MagicMock()
    mock_issue.fields = {"System.AssignedTo": {"displayName": "Bob"}}

    result = tracker._get_assignee(mock_issue)
    assert result == "Bob"


@patch("azure.devops.connection.Connection")
@patch("msrest.authentication.BasicAuthentication")
def test_get_assignee_no_assignee(mock_auth, mock_connection_cls, mock_connection):
    """_get_assignee should return None when no assignee info exists."""
    mock_connection_cls.return_value = mock_connection
    tracker = AzureTracker(
        url="https://dev.azure.com/myorg ",
        token="secrettoken",
        project="MyProject",
        team="MyTeam",
    )
    mock_issue = MagicMock()
    mock_issue.fields = {}

    result = tracker._get_assignee(mock_issue)
    assert result is None


@patch.object(AzureTracker, "import_error", side_effect=SystemExit)
def test_import_error_called_when_azure_missing(mock_import_error):
    """Should call import_error() when azure-devops is not installed."""
    with patch("builtins.__import__", side_effect=ImportError):
        with pytest.raises(SystemExit):
            AzureTracker(
                url="https://dev.azure.com/myorg",
                token="secrettoken",
                project="MyProject",
                team="MyTeam",
            )

    mock_import_error.assert_called_once_with("azure-devops", "azure")
