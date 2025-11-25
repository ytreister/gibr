"""Custom Click group for Gibr CLI."""

import click

from gibr.trackers.jira import JiraTracker
from gibr.trackers.linear import LinearTracker

GLOBAL_FLAGS = ["--verbose"]


class GibrGroup(click.Group):
    """Custom Click group."""

    @staticmethod
    def is_likely_non_digit_issue(arg: str) -> bool:
        """Check if the argument looks like a non-digit issue (e.g. JIRA-123)."""
        return JiraTracker.is_jira_issue(arg) or LinearTracker.is_linear_issue(arg)

    @staticmethod
    def handle_git_alias(args):
        """Handle 'git' alias routing and move global flags to the front."""
        if args and args[0] == "git":
            args.pop(0)

            # Move global flags to the front
            flags = [a for a in args if a in GLOBAL_FLAGS]
            rest = [a for a in args if a not in GLOBAL_FLAGS]
            return flags + rest
        return args

    def handle_create_command(self, args):
        """Insert 'create' command if first arg is numeric or a Jira issue key."""
        # Treat numeric as 'create' (gibr 123 -> gibr create 123)
        for i, arg in enumerate(args):
            if not arg.startswith("--"):
                if arg not in self.commands and (
                    arg.isdigit() or self.is_likely_non_digit_issue(arg)
                ):
                    args.insert(i, "create")
                break
        return args

    def parse_args(self, ctx, args):
        """Parse args to handle 'git' alias routing and default command (create)."""
        args[:] = self.handle_git_alias(args)
        args = self.handle_create_command(args)
        return super().parse_args(ctx, args)
