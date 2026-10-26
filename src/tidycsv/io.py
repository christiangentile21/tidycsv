"""Loading and saving CSV files with clear, user-friendly errors."""

from pathlib import Path

import pandas as pd


class CsvLoadError(Exception):
    """Raised when a CSV file cannot be loaded."""


class CsvWriteError(Exception):
    """Raised when a CSV file cannot be written."""


def load_csv(path: str | Path) -> pd.DataFrame:
    """Read a UTF-8 CSV file into a DataFrame.

    Raises CsvLoadError if the file is missing, empty, not UTF-8,
    or not valid CSV.
    """
    path = Path(path)
    if not path.is_file():
        raise CsvLoadError(f"File not found: {path}")

    try:
        return pd.read_csv(path, encoding="utf-8")
    except pd.errors.EmptyDataError:
        raise CsvLoadError(f"File is empty: {path}") from None
    except UnicodeDecodeError:
        raise CsvLoadError(f"File is not valid UTF-8 text: {path}") from None
    except pd.errors.ParserError as error:
        raise CsvLoadError(f"Could not parse CSV {path}: {error}") from None


def save_csv(df: pd.DataFrame, path: str | Path) -> None:
    """Write a DataFrame to a UTF-8 CSV file without the index column.

    Raises CsvWriteError if the file cannot be written (for example,
    the folder does not exist).
    """
    try:
        df.to_csv(path, index=False, encoding="utf-8")
    except OSError as error:
        raise CsvWriteError(f"Could not write {path}: {error.strerror}") from None
