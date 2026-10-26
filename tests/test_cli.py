import argparse
from pathlib import Path

import pytest

from tidycsv.cli import main, parse_delimiter


def test_summary_prints_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "people.csv"
    path.write_text("name,age\nAna,30\nBen,\n", encoding="utf-8")

    exit_code = main(["summary", str(path)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Rows: 2" in output
    assert "Columns: 2" in output
    assert "age" in output
    assert "Mean" in output


def test_summary_missing_file_returns_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main(["summary", str(tmp_path / "nope.csv")])

    assert exit_code == 2
    assert "File not found" in capsys.readouterr().err


def test_no_command_is_usage_error() -> None:
    with pytest.raises(SystemExit) as info:
        main([])

    assert info.value.code == 2


def test_clean_drops_duplicates_and_writes_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "in.csv"
    target = tmp_path / "out.csv"
    source.write_text("name,age\nAna,30\nBen,25\nAna,30\n", encoding="utf-8")

    exit_code = main(["clean", str(source), "--drop-duplicates", "-o", str(target)])

    assert exit_code == 0
    assert "Removed 1 duplicate row(s)." in capsys.readouterr().out
    assert target.read_text(encoding="utf-8").splitlines() == ["name,age", "Ana,30", "Ben,25"]


def test_clean_without_steps_is_an_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "out.csv"

    exit_code = main(["clean", "in.csv", "-o", str(target)])

    assert exit_code == 2
    assert "nothing to do" in capsys.readouterr().err
    assert not target.exists()


def test_clean_requires_output() -> None:
    with pytest.raises(SystemExit) as info:
        main(["clean", "in.csv", "--drop-duplicates"])

    assert info.value.code == 2


def test_clean_fill_median_reports_unfilled_columns(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "in.csv"
    target = tmp_path / "out.csv"
    source.write_text("city,score\nRome,1\nOslo,\n,9\n", encoding="utf-8")

    exit_code = main(["clean", str(source), "--fill-missing", "median", "-o", str(target)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Filled 1 missing value(s) using median." in output
    assert "Not filled (non-numeric or all missing): city (1)" in output
    assert target.read_text(encoding="utf-8").splitlines()[2] == "Oslo,5.0"


def test_clean_fill_drop_reports_dropped_rows(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "in.csv"
    target = tmp_path / "out.csv"
    source.write_text("a,b\n1,2\n3,\n", encoding="utf-8")

    main(["clean", str(source), "--fill-missing", "drop", "-o", str(target)])

    assert "Dropped 1 row(s) with missing values." in capsys.readouterr().out


def test_clean_rejects_unknown_strategy() -> None:
    with pytest.raises(SystemExit) as info:
        main(["clean", "in.csv", "--fill-missing", "average", "-o", "out.csv"])

    assert info.value.code == 2


def test_check_clean_file_exits_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "good.csv"
    path.write_text("name,age\nAna,30\nBen,25\n", encoding="utf-8")

    exit_code = main(["check", str(path)])

    assert exit_code == 0
    assert "No issues found." in capsys.readouterr().out


def test_check_reports_issues_and_exits_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("name,age\nAna,30\nAna,30\nBen,\n", encoding="utf-8")

    exit_code = main(["check", str(path)])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "1 duplicate row(s)" in output
    assert "age (1)" in output


def test_check_unreadable_file_exits_two(tmp_path: Path) -> None:
    assert main(["check", str(tmp_path / "nope.csv")]) == 2


def test_clean_fill_drop_reports_all_missing_column(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "in.csv"
    target = tmp_path / "out.csv"
    source.write_text("name,age,notes\nAna,30,\nBen,,\n", encoding="utf-8")

    main(["clean", str(source), "--fill-missing", "drop", "-o", str(target)])

    output = capsys.readouterr().out
    assert "Dropped all-missing column(s): notes" in output
    assert "Dropped 1 row(s) with missing values." in output
    assert target.read_text(encoding="utf-8").splitlines() == ["name,age", "Ana,30.0"]


def test_summary_text_only_file_skips_numeric_table(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "cities.csv"
    path.write_text("city\nRome\nOslo\n", encoding="utf-8")

    main(["summary", str(path)])

    output = capsys.readouterr().out
    assert "city" in output
    assert "Mean" not in output


def test_check_missing_only_has_no_duplicate_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "gaps.csv"
    path.write_text("name,age\nAna,30\nBen,\n", encoding="utf-8")

    exit_code = main(["check", str(path)])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "missing values in: age (1)" in output
    assert "duplicate" not in output


def test_check_duplicates_only_has_no_missing_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "dupes.csv"
    path.write_text("name,age\nAna,30\nAna,30\n", encoding="utf-8")

    exit_code = main(["check", str(path)])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "1 duplicate row(s)" in output
    assert "missing" not in output


def test_clean_write_error_exits_two(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / "in.csv"
    source.write_text("a\n1\n1\n", encoding="utf-8")
    target = tmp_path / "no_such_dir" / "out.csv"

    exit_code = main(["clean", str(source), "--drop-duplicates", "-o", str(target)])

    assert exit_code == 2
    assert "Could not write" in capsys.readouterr().err


def test_clean_removes_duplicates_before_filling(tmp_path: Path) -> None:
    # Three copies of Ana would pull the median down to 1 if kept.
    source = tmp_path / "in.csv"
    target = tmp_path / "out.csv"
    source.write_text(
        "name,score\nAna,1\nAna,1\nAna,1\nBen,10\nCara,\nDan,20\n", encoding="utf-8"
    )

    main(
        ["clean", str(source), "--drop-duplicates", "--fill-missing", "median", "-o", str(target)]
    )

    assert "Cara,10.0" in target.read_text(encoding="utf-8").splitlines()


def test_clean_fill_mean_via_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / "in.csv"
    target = tmp_path / "out.csv"
    source.write_text("id,score\n1,1\n2,\n3,5\n", encoding="utf-8")

    main(["clean", str(source), "--fill-missing", "mean", "-o", str(target)])

    assert "Filled 1 missing value(s) using mean." in capsys.readouterr().out
    assert target.read_text(encoding="utf-8").splitlines()[2] == "2,3.0"


def test_clean_fill_mode_via_cli_fills_text(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "in.csv"
    target = tmp_path / "out.csv"
    source.write_text("id,city\n1,Rome\n2,Rome\n3,\n", encoding="utf-8")

    main(["clean", str(source), "--fill-missing", "mode", "-o", str(target)])

    output = capsys.readouterr().out
    assert "Filled 1 missing value(s) using mode." in output
    assert "Not filled" not in output
    assert target.read_text(encoding="utf-8").splitlines()[3] == "3,Rome"


@pytest.mark.parametrize(("value", "expected"), [(";", ";"), ("|", "|"), ("tab", "\t"), ("\t", "\t")])
def test_parse_delimiter_accepts(value: str, expected: str) -> None:
    assert parse_delimiter(value) == expected


@pytest.mark.parametrize("value", ["", ";;", '"', "\n"])
def test_parse_delimiter_rejects(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        parse_delimiter(value)


def test_invalid_delimiter_is_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as info:
        main(["summary", "in.csv", "--delimiter", ";;"])

    assert info.value.code == 2
    assert "single character" in capsys.readouterr().err


def test_summary_with_semicolon_delimiter(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "semi.csv"
    path.write_text("name;age\nAna;30\nBen;25\n", encoding="utf-8")

    main(["summary", str(path), "--delimiter", ";"])

    assert "Columns: 2" in capsys.readouterr().out


def test_check_with_tab_delimiter(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "dupes.tsv"
    path.write_text("name\tage\nAna\t30\nAna\t30\n", encoding="utf-8")

    exit_code = main(["check", str(path), "--delimiter", "tab"])

    assert exit_code == 1
    assert "1 duplicate row(s)" in capsys.readouterr().out


def test_clean_keeps_input_delimiter(tmp_path: Path) -> None:
    source = tmp_path / "in.csv"
    target = tmp_path / "out.csv"
    source.write_text("name;age\nAna;30\nAna;30\n", encoding="utf-8")

    main(["clean", str(source), "--delimiter", ";", "--drop-duplicates", "-o", str(target)])

    assert target.read_text(encoding="utf-8").splitlines() == ["name;age", "Ana;30"]
