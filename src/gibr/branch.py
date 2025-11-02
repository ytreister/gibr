"""Branch name generation logic."""


class BranchName:
    """Generate branch names based on config and issue info."""

    def __init__(self, format_string: str):
        """Construct BranchName object."""
        self.format = format_string

    def generate(self, issue) -> str:
        """Return formatted branch name."""
        # The config placeholders match keys in this mapping
        data = {
            "issuetype": issue.type,
            "issue": issue.id,
            "title": issue.sanitized_title,
            "assignee": issue.assignee,
        }

        # Simple Python str.format expansion
        try:
            branch_name = self.format.format(**data)
        except KeyError as e:
            raise ValueError(f"Unknown placeholder in format: {e.args[0]}")

        return branch_name
