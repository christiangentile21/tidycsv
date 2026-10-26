from pathlib import Path

import pytest

from tidycsv.cli import main


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
