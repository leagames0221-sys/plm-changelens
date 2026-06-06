"""R6: CLI end-to-end (deterministic, no LLM, no network)."""

from __future__ import annotations

import json
from pathlib import Path

from plm_changelens.cli import main

FIX = Path(__file__).parent / "fixtures"
OLD = str(FIX / "bom_old.csv")
NEW = str(FIX / "bom_new.csv")


def test_cli_human_output(capsys):
    rc = main(["diff", OLD, NEW])
    out = capsys.readouterr().out
    assert rc == 0
    assert "BOM change report" in out
    assert "PART-330" in out  # added
    assert "PART-110" in out  # removed


def test_cli_json_output_is_valid_and_complete(capsys):
    rc = main(["diff", OLD, NEW, "--format", "json"])
    out = capsys.readouterr().out
    assert rc == 0
    data = json.loads(out)
    assert data["counts"] == {
        "part_added": 1,
        "part_removed": 1,
        "quantity_changed": 1,
        "revision_updated": 1,
    }
    assert len(data["changes"]) == 4


def test_cli_bad_file_returns_exit_2(capsys):
    rc = main(["diff", OLD, str(FIX / "does_not_exist.csv")])
    err = capsys.readouterr().err
    assert rc == 2
    assert "error:" in err
