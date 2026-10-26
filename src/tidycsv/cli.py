"""Command-line entry point for tidycsv."""

import argparse
import sys
from typing import Any

from tidycsv import __version__
from tidycsv.io import CsvLoadError, load_csv
from tidycsv.summary import summarize

# Exit code for errors such as an unreadable file (argparse also uses 2).
EXIT_ERROR = 2


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser with one subcommand per feature."""
    parser = argparse.ArgumentParser(
        prog="tidycsv",
        description="Inspect, clean, and summarize CSV files.",
    )
    parser.add_argument("--version", action="version", version=f"tidycsv {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_parser = subparsers.add_parser(
        "summary", help="Show rows, columns, types, missing values, and numeric stats."
    )
    summary_parser.add_argument("path", help="CSV file to read.")
    summary_parser.set_defaults(func=run_summary)
    return parser


def run_summary(args: argparse.Namespace) -> int:
    """Handle `tidycsv summary`."""
    df = load_csv(args.path)
    print(format_summary(summarize(df)))
    return 0


def format_summary(summary: dict[str, Any]) -> str:
    """Turn the dict from summarize() into readable text."""
    width = max([len("Column")] + [len(column) for column in summary["dtypes"]])
    lines = [f"Rows: {summary['rows']}", f"Columns: {summary['columns']}", ""]
    lines += format_column_table(summary, width)
    if summary["numeric"]:
        lines += [""] + format_numeric_table(summary["numeric"], width)
    return "\n".join(lines)


def format_column_table(summary: dict[str, Any], width: int) -> list[str]:
    """One line per column: name, dtype, missing count."""
    lines = [f"{'Column':<{width}}  {'Type':<10}  Missing"]
    for column, dtype in summary["dtypes"].items():
        lines.append(f"{column:<{width}}  {dtype:<10}  {summary['missing'][column]}")
    return lines


def format_numeric_table(numeric: dict[str, dict[str, float]], width: int) -> list[str]:
    """One line per numeric column: name, min, max, mean."""
    lines = [f"{'Column':<{width}}  {'Min':>10}  {'Max':>10}  {'Mean':>10}"]
    for column, stats in numeric.items():
        lines.append(
            f"{column:<{width}}  {stats['min']:>10.4g}  {stats['max']:>10.4g}  {stats['mean']:>10.4g}"
        )
    return lines


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run the chosen command. Returns the exit code."""
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except CsvLoadError as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_ERROR
