"""Command-line entry point for tidycsv."""

import argparse
import sys
from typing import Any

import pandas as pd

from tidycsv import __version__
from tidycsv.clean import FILL_STRATEGIES, drop_duplicates, fill_missing
from tidycsv.io import CsvLoadError, CsvWriteError, load_csv, save_csv
from tidycsv.summary import find_issues, has_issues, summarize

# Exit code when `check` finds quality issues.
EXIT_ISSUES = 1
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
    add_input_arguments(summary_parser)
    summary_parser.set_defaults(func=run_summary)

    clean_parser = subparsers.add_parser("clean", help="Write a cleaned copy of a CSV file.")
    add_input_arguments(clean_parser)
    clean_parser.add_argument("-o", "--output", required=True, help="Where to write the result.")
    clean_parser.add_argument(
        "--drop-duplicates", action="store_true", help="Remove fully duplicated rows."
    )
    clean_parser.add_argument(
        "--fill-missing",
        choices=FILL_STRATEGIES,
        help="Fill missing values (mean/median: numeric columns only), or drop "
        "all-missing columns and then incomplete rows.",
    )
    clean_parser.set_defaults(func=run_clean)

    check_parser = subparsers.add_parser(
        "check", help="Exit with code 1 if duplicates or missing values are found."
    )
    add_input_arguments(check_parser)
    check_parser.set_defaults(func=run_check)
    return parser


def add_input_arguments(subparser: argparse.ArgumentParser) -> None:
    """Add the arguments every command shares: the file and its delimiter."""
    subparser.add_argument("path", help="CSV file to read.")
    subparser.add_argument(
        "--delimiter",
        type=parse_delimiter,
        default=",",
        help='Column separator, one character (default ","). Use "tab" or "\\t" for tabs.',
    )


def parse_delimiter(value: str) -> str:
    """Validate --delimiter: one character, with "tab" and "\\t" meaning a tab."""
    if value in ("tab", "\\t"):
        return "\t"
    if len(value) != 1:
        raise argparse.ArgumentTypeError(f"must be a single character, got {value!r}")
    if value in ('"', "\n", "\r"):
        raise argparse.ArgumentTypeError(f"{value!r} can't be used as a delimiter")
    return value


def run_summary(args: argparse.Namespace) -> int:
    """Handle `tidycsv summary`."""
    df = load_csv(args.path, args.delimiter)
    print(format_summary(summarize(df)))
    return 0


def run_clean(args: argparse.Namespace) -> int:
    """Handle `tidycsv clean`: apply the chosen steps, then save.

    Duplicates are removed first so they don't skew the mean/median/mode.
    The output uses the same delimiter as the input.
    """
    if not (args.drop_duplicates or args.fill_missing):
        print("Error: nothing to do. Pass --drop-duplicates and/or --fill-missing.", file=sys.stderr)
        return EXIT_ERROR

    df = load_csv(args.path, args.delimiter)
    if args.drop_duplicates:
        rows_before = len(df)
        df = drop_duplicates(df)
        print(f"Removed {rows_before - len(df)} duplicate row(s).")
    if args.fill_missing:
        df = run_fill_step(df, args.fill_missing)

    save_csv(df, args.output, args.delimiter)
    print(f"Wrote {len(df)} row(s) to {args.output}")
    return 0


def run_fill_step(df: pd.DataFrame, strategy: str) -> pd.DataFrame:
    """Apply fill_missing() and print what it changed."""
    rows_before = len(df)
    columns_before = list(df.columns)
    missing_before = int(df.isna().sum().sum())
    df = fill_missing(df, strategy)

    if strategy == "drop":
        dropped_columns = [column for column in columns_before if column not in df.columns]
        if dropped_columns:
            print(f"Dropped all-missing column(s): {', '.join(dropped_columns)}")
        print(f"Dropped {rows_before - len(df)} row(s) with missing values.")
    else:
        filled = missing_before - int(df.isna().sum().sum())
        print(f"Filled {filled} missing value(s) using {strategy}.")

    still_missing = df.isna().sum()
    still_missing = still_missing[still_missing > 0]
    if not still_missing.empty:
        print(f"Not filled (non-numeric or all missing): {format_counts(still_missing.to_dict())}")
    return df


def run_check(args: argparse.Namespace) -> int:
    """Handle `tidycsv check`: print a short report, return 0 or EXIT_ISSUES."""
    issues = find_issues(load_csv(args.path, args.delimiter))
    if not has_issues(issues):
        print("No issues found.")
        return 0

    print("Issues found:")
    if issues["duplicate_rows"]:
        print(f"  - {issues['duplicate_rows']} duplicate row(s)")
    if issues["missing"]:
        print(f"  - missing values in: {format_counts(issues['missing'])}")
    return EXIT_ISSUES


def format_counts(counts: dict[str, int]) -> str:
    """Format {"age": 1, "score": 2} as "age (1), score (2)"."""
    return ", ".join(f"{column} ({count})" for column, count in counts.items())


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
