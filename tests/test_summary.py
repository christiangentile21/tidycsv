import math

import pandas as pd

from tidycsv.summary import find_issues, has_issues, summarize


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


def test_find_issues_reports_duplicates_and_missing() -> None:
    df = pd.DataFrame({"name": ["Ana", "Ana", "Ben"], "age": [30, 30, None]})

    issues = find_issues(df)

    assert issues == {"duplicate_rows": 1, "missing": {"age": 1}}
    assert has_issues(issues)


def test_clean_frame_has_no_issues() -> None:
    df = pd.DataFrame({"name": ["Ana", "Ben"], "age": [30, 25]})

    issues = find_issues(df)

    assert issues == {"duplicate_rows": 0, "missing": {}}
    assert not has_issues(issues)


def test_empty_frame_has_no_issues() -> None:
    assert not has_issues(find_issues(pd.DataFrame(columns=["a", "b"])))


def test_rows_of_only_missing_values_count_as_duplicates() -> None:
    df = pd.DataFrame({"a": [None, None]})

    assert find_issues(df) == {"duplicate_rows": 1, "missing": {"a": 2}}
