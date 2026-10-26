"""Command-line entry point for tidycsv."""

import argparse
import sys
from typing import Any

import pandas as pd

from tidycsv import __version__
from tidycsv.clean import FILL_STRATEGIES, drop_duplicates, fill_missing
from tidycsv.io import CsvLoadError, CsvWriteError, load_csv, save_csv
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

    clean_parser = subparsers.add_parser("clean", help="Write a cleaned copy of a CSV file.")
    clean_parser.add_argument("path", help="CSV file to read.")
    clean_parser.add_argument("-o", "--output", required=True, help="Where to write the result.")
    clean_parser.add_argument(
        "--drop-duplicates", action="store_true", help="Remove fully duplicated rows."
    )
    clean_parser.add_argument(
        "--fill-missing",
        choices=FILL_STRATEGIES,
        help="Fill missing values (mean/median: numeric columns only) or drop those rows.",
    )
    clean_parser.set_defaults(func=run_clean)
    return parser


def run_summary(args: argparse.Namespace) -> int:
    """Handle `tidycsv summary`."""
    df = load_csv(args.path)
    print(format_summary(summarize(df)))
    return 0


def run_clean(args: argparse.Namespace) -> int:
    """Handle `tidycsv clean`: apply the chosen steps, then save.

    Duplicates are removed first so they don't skew the mean/median/mode.
    """
    if not (args.drop_duplicates or args.fill_missing):
        print("Error: nothing to do. Pass --drop-duplicates and/or --fill-missing.", file=sys.stderr)
        return EXIT_ERROR

    df = load_csv(args.path)
    if args.drop_duplicates:
        rows_before = len(df)
        df = drop_duplicates(df)
        print(f"Removed {rows_before - len(df)} duplicate row(s).")
    if args.fill_missing:
        df = run_fill_step(df, args.fill_missing)

    save_csv(df, args.output)
    print(f"Wrote {len(df)} row(s) to {args.output}")
    return 0


def run_fill_step(df: pd.DataFrame, strategy: str) -> pd.DataFrame:
    """Apply fill_missing() and print what it changed."""
    rows_before = len(df)
    missing_before = int(df.isna().sum().sum())
    df = fill_missing(df, strategy)

    if strategy == "drop":
        print(f"Dropped {rows_before - len(df)} row(s) with missing values.")
    else:
        filled = missing_before - int(df.isna().sum().sum())
        print(f"Filled {filled} missing value(s) using {strategy}.")

    still_missing = df.isna().sum()
    still_missing = still_missing[still_missing > 0]
    if not still_missing.empty:
        listing = ", ".join(f"{column} ({count})" for column, count in still_missing.items())
        print(f"Not filled (non-numeric or all missing): {listing}")
    return df


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
    except (CsvLoadError, CsvWriteError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_ERROR
