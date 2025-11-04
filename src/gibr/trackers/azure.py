"""AzureDevOps issue tracker integration."""

import json
import logging

import click

from gibr.issue import Issue
from gibr.notify import error
from gibr.registry import register_tracker
from gibr.trackers.base import IssueTracker


@register_tracker(
    key="azure",
    display_name="AzureDevOps",
)
class AzureTracker(IssueTracker):
    """Azure issue tracker using azure-devops."""

    def __init__(
        self, url: str, token: str, project: str, team: str, closed_states: list[str]
    ):
        """Initialize AzureTracker with connection to specified project."""
        try:
            from azure.devops.connection import Connection
            from azure.devops.exceptions import AzureDevOpsClientError
            from azure.devops.v7_1.work_item_tracking import Wiql
            from msrest.authentication import BasicAuthentication

            self.AzureDevOpsClientError = AzureDevOpsClientError
            self.Wiql = Wiql
        except ImportError:
            self.import_error("azure-devops", "azure")

        self.url = url
        self.project_name = project
        self.team_name = team
        self.closed_states = closed_states
        try:
            credentials = BasicAuthentication("", token)
            connection = Connection(base_url=url, creds=credentials)

            self.wit_client = connection.clients.get_work_item_tracking_client()
        except Exception as e:
            raise ValueError(f"Failed to connect to Azure: {e}")

    @classmethod
    def configure_interactively(cls) -> dict:
        """Interactively prompt user for Azure configuration."""
        url = click.prompt(
            "Azure base URL (e.g. https://dev.azure.com/YOURORG)",
            default="https://dev.azure.com/YOURORG",
        )
        project = click.prompt("Azure project name (e.g. project)")
        team = click.prompt("Team name for issues (e.g. team)")
        token_var = click.prompt(
            "Environment variable for your Azure Token", default="AZURE_TOKEN"
        )

        cls.check_token(token_var)
        return {
            "url": url,
            "project": project,
            "team": team,
            "token": f"${{{token_var}}}",
        }

    @classmethod
    def from_config(cls, config):
        """Create AzureTracker from config dictionary."""
        try:
            url = config["url"]
            token = config["token"]
            project = config["project"]
            team = config["team"]
            closed_states = json.loads(
                config.get("closed_states", '["Done", "Removed", "Closed"]')
            )
        except json.JSONDecodeError:
            raise ValueError(
                "Unrecognized list format for closed_states; "
                "please check the documentation."
            )
        except KeyError as e:
            raise ValueError(f"Missing key in 'azure' config: {e.args[0]}")
        return cls(
            url=url,
            token=token,
            project=project,
            team=team,
            closed_states=closed_states,
        )

    @classmethod
    def describe_config(cls, config: dict) -> str:
        """Return a short string describing the config."""
        return f"""Azure DevOps:
            URL                : {config.get("url")}
            Project            : {config.get("project")}
            Team               : {config.get("team")}
            Token              : {config.get("token")}
            Closed States      : {
            config.get("closed_states", ["Done", "Removed", "Closed"])
        }"""

    def _build_state_exclusion(self) -> str:
        """Build the state exclusion clause for WIQL query using NOT IN."""
        # Ensure closed_states is a list
        states_list = ", ".join([f"'{state}'" for state in self.closed_states])
        return f"[System.State] NOT IN ({states_list})"

    def _get_assignee(self, issue):
        """Get issue assignee."""
        if getattr(issue, "fields", None) and "System.AssignedTo" in issue.fields:
            return issue.fields["System.AssignedTo"]["displayName"]

        # No assignee found
        return None

    def get_issue(self, issue_id: str) -> dict:
        """Fetch issue details by issue id."""
        try:
            issue = self.wit_client.get_work_item(int(issue_id))
        except self.AzureDevOpsClientError as e:
            logging.debug(f"An exception occured when getting a work item {e}")
            error(f"Issue #{issue_id} was not found")
        except Exception as e:
            logging.debug(f"Failed to get issue : {e}")
            error("Failed to get issue, run again with --verbose flag for more details")
        return Issue(
            id=issue.id,
            title=issue.fields["System.Title"],
            type=issue.fields["System.WorkItemType"],
            assignee=self._get_assignee(issue),
        )

    def list_issues(self) -> list[dict]:
        """List all open issues in the project."""
        state_exclusion = self._build_state_exclusion()

        wiql = self.Wiql(
            query=rf"""
            SELECT [System.Id]
            FROM WorkItems
            WHERE
            [System.IterationPath] = @CurrentIteration(
                '[{self.project_name}]\{self.team_name}'
                ) AND
            [System.TeamProject] = '{self.project_name}' AND
            {state_exclusion}
            ORDER BY [System.ChangedDate] DESC"""
        )
        try:
            query_result = self.wit_client.query_by_wiql(wiql)
        except Exception as e:
            logging.debug(f"Failed to get issue ids : {e}")
            error(
                "Failed to get issues, run again with --verbose flag for more details"
            )

        work_items = getattr(query_result, "work_items", None)
        if not work_items:
            return []

        try:
            issues = self.wit_client.get_work_items([item.id for item in work_items])
        except Exception as e:
            logging.debug(f"Failed to get issues: {e}")
            error(
                "Failed to get issues, run again with --verbose flag for more details"
            )

        return [
            Issue(
                id=issue.id,
                title=issue.fields["System.Title"],
                type=issue.fields["System.WorkItemType"],
                assignee=self._get_assignee(issue),
            )
            for issue in issues
        ]
