"""Custom Click group for Gibr CLI."""

import click

from gibr.trackers.jira import JiraTracker


class GibrGroup(click.Group):
    """Custom Click group."""

    def parse_args(self, ctx, args):
        """Parse args to handle 'git' alias routing and default command (create)."""
        # If 'git' alias is present, handle it
        if args and args[0] == "git":
            args.pop(0)

            # Move all flags (starting with '--') to the front
            flags = [a for a in args if a.startswith("--")]
            rest = [a for a in args if not a.startswith("--")]
            args[:] = flags + rest

        # Treat numeric as 'create' (gibr 123 -> gibr create 123)
        for i, arg in enumerate(args):
            if not arg.startswith("--"):
                if arg not in self.commands and (
                    arg.isdigit() or JiraTracker.is_jira_issue(arg)
                ):
                    args.insert(i, "create")
                break

        return super().parse_args(ctx, args)
