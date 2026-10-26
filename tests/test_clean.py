import math

import pandas as pd
import pytest

from tidycsv.clean import all_missing_columns, drop_duplicates, fill_missing


def test_drop_duplicates_keeps_first_occurrence() -> None:
    df = pd.DataFrame({"name": ["Ana", "Ben", "Ana"], "age": [30, 25, 30]})

    result = drop_duplicates(df)

    expected = pd.DataFrame({"name": ["Ana", "Ben"], "age": [30, 25]})
    pd.testing.assert_frame_equal(result, expected)


def test_rows_differing_in_one_column_are_kept() -> None:
    df = pd.DataFrame({"name": ["Ana", "Ana"], "age": [30, 31]})

    assert len(drop_duplicates(df)) == 2


def test_missing_values_count_as_equal() -> None:
    df = pd.DataFrame({"name": ["Ana", "Ana"], "age": [None, None]})

    assert len(drop_duplicates(df)) == 1


def test_no_duplicates_returns_same_rows() -> None:
    df = pd.DataFrame({"x": [1, 2, 3]})

    pd.testing.assert_frame_equal(drop_duplicates(df), df)


def test_input_frame_is_not_modified() -> None:
    df = pd.DataFrame({"x": [1, 1]})

    drop_duplicates(df)

    assert len(df) == 2


def mixed_frame() -> pd.DataFrame:
    """Small frame with a skewed numeric column and a text column."""
    return pd.DataFrame(
        {
            "score": [1.0, 2.0, 9.0, None],
            "city": ["Rome", "Oslo", "Rome", None],
        }
    )


def test_fill_mean_fills_numeric_only() -> None:
    result = fill_missing(mixed_frame(), "mean")

    assert result["score"].tolist() == [1.0, 2.0, 9.0, 4.0]
    assert pd.isna(result["city"].iloc[3])


def test_fill_median_uses_middle_value() -> None:
    result = fill_missing(mixed_frame(), "median")

    assert result["score"].iloc[3] == 2.0


def test_fill_mode_fills_text_columns_too() -> None:
    result = fill_missing(mixed_frame(), "mode")

    assert result["city"].iloc[3] == "Rome"
    assert not result.isna().any().any()


def test_fill_mode_tie_picks_smallest_value() -> None:
    df = pd.DataFrame({"x": [3.0, 1.0, None]})

    assert fill_missing(df, "mode")["x"].iloc[2] == 1.0


def test_fill_drop_removes_incomplete_rows() -> None:
    result = fill_missing(mixed_frame(), "drop")

    assert len(result) == 3
    assert list(result.index) == [0, 1, 2]


def test_all_missing_column_is_left_unchanged() -> None:
    df = pd.DataFrame({"x": [1.0, None], "empty": [None, None]})

    for strategy in ("mean", "median", "mode"):
        result = fill_missing(df, strategy)
        assert result["x"].tolist() == [1.0, 1.0]
        assert result["empty"].isna().all()


def test_drop_removes_all_missing_column_and_keeps_rows() -> None:
    df = pd.DataFrame({"x": [1.0, 2.0, None], "empty": [None, None, None]})

    result = fill_missing(df, "drop")

    expected = pd.DataFrame({"x": [1.0, 2.0]})
    pd.testing.assert_frame_equal(result, expected)


def test_drop_on_header_only_frame_keeps_columns() -> None:
    df = pd.DataFrame(columns=["a", "b"])

    result = fill_missing(df, "drop")

    assert list(result.columns) == ["a", "b"]
    assert result.empty


def test_drop_when_every_column_is_missing_keeps_header_only() -> None:
    df = pd.DataFrame({"a": [None, None], "b": [None, None]})

    result = fill_missing(df, "drop")

    assert list(result.columns) == ["a", "b"]
    assert result.empty


def test_all_missing_columns_lists_only_fully_missing() -> None:
    df = pd.DataFrame({"some": [1.0, None], "none": [None, None]})

    assert all_missing_columns(df) == ["none"]


def test_fill_does_not_modify_input() -> None:
    df = mixed_frame()

    fill_missing(df, "mean")

    assert math.isnan(df["score"].iloc[3])


def test_unknown_strategy_raises() -> None:
    with pytest.raises(ValueError, match="Unknown fill strategy"):
        fill_missing(mixed_frame(), "average")
