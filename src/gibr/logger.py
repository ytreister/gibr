"""Logging configuration for gibr."""

import logging
import sys


def configure_logger(verbose):
    """Set up logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(message)s",
        stream=sys.stdout,
    )
