import runpy
import subprocess
import sys
from pathlib import Path

import pytest

import tidycsv


def test_package_has_version() -> None:
    assert tidycsv.__version__ == "0.1.0"


def test_python_m_tidycsv_returns_check_exit_code(tmp_path: Path) -> None:
    path = tmp_path / "dupes.csv"
    path.write_text("a\n1\n1\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "tidycsv", "check", str(path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "1 duplicate row(s)" in result.stdout


def test_main_module_runs_in_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Same as the subprocess test, but in-process so coverage can see it.
    path = tmp_path / "good.csv"
    path.write_text("a\n1\n2\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["tidycsv", "check", str(path)])

    with pytest.raises(SystemExit) as info:
        runpy.run_module("tidycsv", run_name="__main__")

    assert info.value.code == 0
