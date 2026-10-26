import pandas as pd

from tidycsv.clean import drop_duplicates


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
