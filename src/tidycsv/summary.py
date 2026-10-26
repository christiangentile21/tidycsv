"""Summary statistics for a DataFrame."""

from typing import Any

import pandas as pd


def summarize(df: pd.DataFrame) -> dict[str, Any]:
    """Return row/column counts, dtypes, missing counts, and numeric stats."""
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "dtypes": {str(column): str(dtype) for column, dtype in df.dtypes.items()},
        "missing": {str(column): int(count) for column, count in df.isna().sum().items()},
        "numeric": numeric_stats(df),
    }


def numeric_stats(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Return min, max, and mean for each numeric column.

    Missing values are ignored. A column that is entirely missing gets NaN.
    """
    numeric = df.select_dtypes(include="number")
    return {
        str(column): {
            "min": float(numeric[column].min()),
            "max": float(numeric[column].max()),
            "mean": float(numeric[column].mean()),
        }
        for column in numeric.columns
    }
