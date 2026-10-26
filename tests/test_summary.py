import math

import pandas as pd

from tidycsv.summary import summarize


def test_summarize_counts_and_stats() -> None:
    df = pd.DataFrame({"name": ["Ana", "Ben", None], "age": [30, 20, 25]})

    result = summarize(df)

    assert result["rows"] == 3
    assert result["columns"] == 2
    assert result["dtypes"]["age"] == "int64"
    assert result["missing"] == {"name": 1, "age": 0}
    assert result["numeric"] == {"age": {"min": 20.0, "max": 30.0, "mean": 25.0}}


def test_numeric_stats_ignore_missing_values() -> None:
    df = pd.DataFrame({"score": [1.0, None, 3.0]})

    stats = summarize(df)["numeric"]["score"]

    assert stats == {"min": 1.0, "max": 3.0, "mean": 2.0}


def test_all_missing_numeric_column_gives_nan() -> None:
    df = pd.DataFrame({"score": [float("nan"), float("nan")]})

    stats = summarize(df)["numeric"]["score"]

    assert all(math.isnan(value) for value in stats.values())


def test_text_only_frame_has_no_numeric_stats() -> None:
    df = pd.DataFrame({"city": ["Rome", "Oslo"]})

    assert summarize(df)["numeric"] == {}


def test_empty_frame_keeps_columns() -> None:
    df = pd.DataFrame(columns=["a", "b"])

    result = summarize(df)

    assert result["rows"] == 0
    assert result["columns"] == 2
    assert result["missing"] == {"a": 0, "b": 0}
