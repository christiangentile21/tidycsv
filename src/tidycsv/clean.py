"""Pure cleaning functions: DataFrame in, new DataFrame out."""

from typing import Any

import pandas as pd

FILL_STRATEGIES = ("mean", "median", "mode", "drop")


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy without fully duplicated rows, keeping the first one.

    Two rows count as duplicates only if every column matches; missing
    values in the same column are treated as equal. The index is reset
    to 0..n-1 so the result has no gaps.
    """
    return df.drop_duplicates(keep="first").reset_index(drop=True)


def fill_missing(df: pd.DataFrame, strategy: str) -> pd.DataFrame:
    """Return a copy with missing values handled by the given strategy.

    - "mean" / "median": fill numeric columns only; others are left as is.
    - "mode": fill every column with its most common value.
    - "drop": see drop_missing().

    For mean/median/mode, a column that is entirely missing has no value
    to fill with, so it is left unchanged.
    """
    if strategy == "drop":
        return drop_missing(df)
    return df.fillna(fill_values(df, strategy))


def drop_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with no missing values, removing as little as possible.

    1. Remove rows with no data at all.
    2. Remove columns that are entirely missing (otherwise they would
       force every row to be dropped).
    3. Remove any row that still has a missing value.
    """
    df = df.dropna(how="all")
    df = df.drop(columns=all_missing_columns(df))
    return df.dropna().reset_index(drop=True)


def all_missing_columns(df: pd.DataFrame) -> list[str]:
    """Return the columns where every value is missing.

    A frame with no rows returns [] so a header-only file keeps its columns.
    """
    if df.empty:
        return []
    return [column for column in df.columns if df[column].isna().all()]


def fill_values(df: pd.DataFrame, strategy: str) -> dict[str, Any]:
    """Return {column: value to fill with} for a mean/median/mode strategy."""
    if strategy == "mean":
        return df.select_dtypes(include="number").mean().to_dict()
    if strategy == "median":
        return df.select_dtypes(include="number").median().to_dict()
    if strategy == "mode":
        return column_modes(df)
    raise ValueError(f"Unknown fill strategy: {strategy}")


def column_modes(df: pd.DataFrame) -> dict[str, Any]:
    """Return the most common value per column, skipping all-missing columns.

    On a tie, pandas returns the modes sorted, so the smallest value wins.
    """
    modes = {}
    for column in df.columns:
        column_mode = df[column].mode()
        if not column_mode.empty:
            modes[column] = column_mode.iloc[0]
    return modes
