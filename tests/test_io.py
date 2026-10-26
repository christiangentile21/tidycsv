from pathlib import Path

import pandas as pd
import pytest

from tidycsv.io import CsvLoadError, CsvWriteError, load_csv, save_csv


def test_load_valid_csv(tmp_path: Path) -> None:
    path = tmp_path / "people.csv"
    path.write_text("name,age\nAna,30\nBen,25\n", encoding="utf-8")

    df = load_csv(path)

    assert list(df.columns) == ["name", "age"]
    assert len(df) == 2


def test_header_only_csv_gives_empty_frame(tmp_path: Path) -> None:
    path = tmp_path / "header.csv"
    path.write_text("name,age\n", encoding="utf-8")

    df = load_csv(path)

    assert list(df.columns) == ["name", "age"]
    assert df.empty


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(CsvLoadError, match="File not found"):
        load_csv(tmp_path / "nope.csv")


def test_directory_is_not_a_file(tmp_path: Path) -> None:
    with pytest.raises(CsvLoadError, match="File not found"):
        load_csv(tmp_path)


def test_empty_file_raises(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")

    with pytest.raises(CsvLoadError, match="File is empty"):
        load_csv(path)


def test_bad_encoding_raises(tmp_path: Path) -> None:
    path = tmp_path / "latin1.csv"
    path.write_bytes("name\ncafé\n".encode("latin-1"))

    with pytest.raises(CsvLoadError, match="not valid UTF-8"):
        load_csv(path)


def test_malformed_csv_raises(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("a,b\n1,2\n3,4,5\n", encoding="utf-8")

    with pytest.raises(CsvLoadError, match="Could not parse"):
        load_csv(path)


def test_save_then_load_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "out.csv"
    df = pd.DataFrame({"name": ["Ana", "Ben"], "age": [30, 25]})

    save_csv(df, path)

    assert path.read_text(encoding="utf-8").splitlines()[0] == "name,age"
    pd.testing.assert_frame_equal(load_csv(path), df)


def test_save_to_missing_folder_raises(tmp_path: Path) -> None:
    with pytest.raises(CsvWriteError, match="Could not write"):
        save_csv(pd.DataFrame({"x": [1]}), tmp_path / "no_such_dir" / "out.csv")


def test_load_with_semicolon_delimiter(tmp_path: Path) -> None:
    path = tmp_path / "semi.csv"
    path.write_text("name;age\nAna;30\n", encoding="utf-8")

    df = load_csv(path, delimiter=";")

    assert list(df.columns) == ["name", "age"]
    assert df["age"].iloc[0] == 30


def test_save_with_tab_delimiter(tmp_path: Path) -> None:
    path = tmp_path / "out.tsv"
    df = pd.DataFrame({"name": ["Ana"], "age": [30]})

    save_csv(df, path, delimiter="\t")

    assert path.read_text(encoding="utf-8").splitlines() == ["name\tage", "Ana\t30"]
    pd.testing.assert_frame_equal(load_csv(path, delimiter="\t"), df)
