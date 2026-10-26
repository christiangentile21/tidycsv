"""Command-line entry point for tidycsv."""

import argparse

from tidycsv import __version__


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="tidycsv",
        description="Inspect, clean, and summarize CSV files.",
    )
    parser.add_argument("--version", action="version", version=f"tidycsv {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run the chosen command. Returns the exit code."""
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0
