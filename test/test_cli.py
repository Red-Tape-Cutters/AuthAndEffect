"""Tests for the authandeffect command-line interface."""

import pytest

from authandeffect.cli import main


def test_sources_lists_registry(capsys):
    """'sources' prints one line per registry entry and exits 0."""
    assert main(["sources"]) == 0
    out = capsys.readouterr().out
    assert "humana-ma" in out and "kaiser-ma" in out


def test_summary_on_seed(capsys):
    """'summary' prints denial rates for the seed data."""
    assert main(["summary"]) == 0
    out = capsys.readouterr().out
    assert "5 reporting entities" in out
    assert "H0029" in out


def test_validate_seed_passes(capsys):
    """'validate' on the seed reports only warnings and exits 0."""
    assert main(["validate"]) == 0
    assert "errors: 0" in capsys.readouterr().out


def test_validate_clean_file(tmp_path, minimal, capsys):
    """A file with no issues prints OK."""
    path = tmp_path / "clean.csv"
    minimal.to_csv(path, index=False)
    assert main(["validate", str(path)]) == 0
    assert capsys.readouterr().out.startswith("OK")


def test_validate_bad_file_exits_1(tmp_path, minimal):
    """Error-level issues produce exit code 1."""
    minimal.loc[0, "value"] = 150
    path = tmp_path / "bad.csv"
    minimal.to_csv(path, index=False)
    assert main(["validate", str(path)]) == 1


def test_validate_missing_columns_exits_2(tmp_path, capsys):
    """A file that is not in the schema exits 2 with a message."""
    path = tmp_path / "wrong.csv"
    path.write_text("a,b\n1,2\n")
    assert main(["validate", str(path)]) == 2
    assert "missing required columns" in capsys.readouterr().err


def test_validate_missing_file_exits_2(tmp_path):
    """A path that does not exist exits 2."""
    assert main(["validate", str(tmp_path / "nope.csv")]) == 2


def test_version_flag(capsys):
    """--version prints the package version."""
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "0.1.0" in capsys.readouterr().out
