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
