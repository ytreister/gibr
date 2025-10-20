"""Configuration handling for gibr."""

import logging
from configparser import BasicInterpolation, ConfigParser
from os import path
from pathlib import Path

from gibr.notify import error


class EnvInterpolation(BasicInterpolation):
    """Expand environment variables inside .gibrconfig."""

    def before_get(self, parser, section, option, value, defaults):
        """Overload before_get method."""
        value = super().before_get(parser, section, option, value, defaults)
        return path.expandvars(value)


class GibrConfig:
    """Handle loading and storing gibr configurations."""

    CONFIG_FILENAME = ".gibrconfig"

    def __init__(self):
        """Construct GibrConfig object."""
        self.config_file = None
        self.config = {}

    def _find_config_file(self):
        """Search for config file.

        Search the current directory and all parent directories until config file
        is found then return the path to the file or None if not found
        """
        d = Path.cwd()
        root = Path(d.root)
        while d != root:
            logging.debug(f"Looking for .gibrconfig in {d}")
            attempt = d / self.CONFIG_FILENAME
            if attempt.exists():
                logging.debug(f"Found config file: {attempt}")
                return attempt
            if d == d.parent:
                return None
            d = d.parent
        return None

    def _get_tracker_details_str(self):
        """Get tracker details string for __str__."""
        tracker_type = self.config.get("issue-tracker", {}).get("name")
        if tracker_type == "github":
            return f"""Github:
        Repo               : {self.config.get("github", {}).get("repo")}
        Token              : {self.config.get("github", {}).get("token")}"""
        elif tracker_type == "jira":
            return f"""Jira:
        URL                : {self.config.get("jira", {}).get("url")}
        Project Key        : {self.config.get("jira", {}).get("project_key")}
        User               : {self.config.get("jira", {}).get("user")}
        Token              : {self.config.get("jira", {}).get("token")}"""
        else:
            return ""

    def __str__(self):
        """Stringify."""
        return f"""Gibr Configuration:
    Default:
        Branch Name Format : {self.config.get("DEFAULT", {}).get("branch_name_format")}
    Issue Tracker:
        Name               : {self.config.get("issue-tracker", {}).get("name")}
    {self._get_tracker_details_str()}"""

    def load(self):
        """Load .gibrconfig into a simple dictionary."""
        config_file = self._find_config_file()
        if not config_file:
            error(f"{self.CONFIG_FILENAME} not found in this or any parent directory")

        parser = ConfigParser(interpolation=EnvInterpolation())
        parser.read(config_file)
        self.config_file = config_file

        config = {}
        for section in parser.sections():
            config[section] = dict(parser.items(section))
        # DEFAULT section is special
        if parser.defaults():
            config["DEFAULT"] = dict(parser.defaults())

        self.config = config
        logging.debug(str(self))
        return self
