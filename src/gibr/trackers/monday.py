"""Monday.dev issue tracker implementation."""

import re

import click
from slugify import slugify

from gibr.issue import Issue
from gibr.notify import error
from gibr.registry import register_tracker

from .base import IssueTracker


@register_tracker(key="monday", display_name="Monday.dev", numeric_issues=False)
class MondayTracker(IssueTracker):
    """monday.dev issue tracker."""

    API_URL = "https://api.monday.com/v2"

    def __init__(self, token: str, board_id: str):
        """Construct MondayTracker object."""
        self.token = token
        self.board_id = board_id

        if not re.match(r"^\d+$", str(board_id)):
            error(f"Invalid board ID: {board_id}. Must be numeric.")

    @classmethod
    def configure_interactively(cls) -> dict:
        """Prompt user for monday.dev configuration."""
        board_id = click.prompt("Monday board ID (numeric, required)").strip()
        if not re.match(r"^\d+$", board_id):
            error("Board ID must be numeric.")

        token_var = click.prompt(
            "Environment variable for your Monday API token",
            default="MONDAY_TOKEN",
        )
        cls.check_token(token_var)

        return {"board_id": board_id, "token": f"${{{token_var}}}"}

    @classmethod
    def from_config(cls, config: dict):
        """Create MondayTracker from config dictionary."""
        try:
            board_id = config["board_id"]
            token = config["token"]
        except KeyError as e:
            raise ValueError(f"Missing key in 'monday' config: {e.args[0]}")
        return cls(token=token, board_id=board_id)

    @classmethod
    def describe_config(cls, config: dict) -> str:
        """Return a configuration summary for CLI display."""
        return f"""Monday.dev:
        Board ID           : {config.get("board_id")}
        Token              : {config.get("token")}"""

    def _get_assignee(self, item):
        """Extract assignee from monday.dev item."""
        for col in item.get("column_values", []):
            if col.get("type") == "people":
                return slugify(col.get("text")) or None
        return None

    def get_issue(self, issue_id: str):
        """Fetch issue details by item ID."""
        if not issue_id.isdigit():
            error(
                f"Monday.dev requires numeric item IDs. Received: {issue_id}\n"
                f"You may need to use the visible Item ID from the board URL."
            )

        query = """
            query ($item_id: ID!) {
            items(ids: [$item_id]) {
                id
                name
                column_values {
                id
                type
                text
                value
                }
            }
            }
        """

        data = self._graphql_request(
            query, {"board_id": int(self.board_id), "item_id": int(issue_id)}
        )
        items = data.get("items", [])

        if not items:
            error(f"Issue {issue_id} not found on Monday board {self.board_id}.")

        item = items[0]

        return Issue(
            id=item["id"],
            title=item["name"],
            assignee=self._get_assignee(item),
        )

    def list_issues(self):
        """List open issues on a monday.dev board."""
        query = """
query ($board_id: ID!) {
  boards(ids: [$board_id]) {
    id
    name
    items_page(limit: 500) {
      items {
        id
        name
        column_values {
          id
          type
          text
          value
        }
      }
    }
  }
}
        """

        data = self._graphql_request(query, {"board_id": int(self.board_id)})
        boards = data.get("boards", [])

        if not boards:
            error(f"Board {self.board_id} not found or inaccessible.")
        items = boards[0]["items_page"]["items"]

        results = []

        for item in items:
            status = None
            for col in item.get("column_values", []):
                if col.get("title", "").lower() == "task_status":
                    status = col.get("text")
                    break

            # Only return issues not marked as Done/Completed
            if status and status.lower() in ("done", "complete", "completed"):
                continue

            results.append(
                Issue(
                    id=item["id"],
                    title=item["name"],
                    assignee=self._get_assignee(item),
                )
            )

        return results
