"""R1.1-R1.3: BOM CSV loading and validation (no silent guessing)."""

from __future__ import annotations

from pathlib import Path

import pytest

from plm_changelens.core.tree import size
from plm_changelens.packs.plm.bom_loader import BomFormatError, load_bom_csv

FIX = Path(__file__).parent / "fixtures"


def _write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_load_valid_bom_builds_tree():
    root = load_bom_csv(FIX / "bom_old.csv")
    assert root.label == "ASSY-100"
    # ASSY-100 + SUB-210 + PART-310 + PART-320 + PART-110 = 5 nodes
    assert size(root) == 5
    # SUB-210 has two children; the cover is a direct child of the root.
    labels = {c.label for c in root.children}
    assert labels == {"SUB-210", "PART-110"}


def test_path_is_recorded_for_descendants():
    root = load_bom_csv(FIX / "bom_old.csv")
    sub = next(c for c in root.children if c.label == "SUB-210")
    screw = next(c for c in sub.children if c.label == "PART-310")
    assert screw.payload.path == ["ASSY-100", "SUB-210"]


def test_missing_required_column_raises(tmp_path):
    p = _write(tmp_path, "bad.csv", "level,part_number,quantity\n0,A,1\n")
    with pytest.raises(BomFormatError, match="revision"):
        load_bom_csv(p)


def test_non_numeric_quantity_raises_with_row(tmp_path):
    p = _write(
        tmp_path, "bad.csv",
        "level,part_number,quantity,revision\n0,A,xyz,A\n",
    )
    with pytest.raises(BomFormatError) as exc:
        load_bom_csv(p)
    assert exc.value.row == 2


def test_skipped_level_raises(tmp_path):
    p = _write(
        tmp_path, "bad.csv",
        "level,part_number,quantity,revision\n0,A,1,A\n2,B,1,A\n",
    )
    with pytest.raises(BomFormatError, match="parent"):
        load_bom_csv(p)


def test_multiple_roots_raises(tmp_path):
    p = _write(
        tmp_path, "bad.csv",
        "level,part_number,quantity,revision\n0,A,1,A\n0,B,1,A\n",
    )
    with pytest.raises(BomFormatError, match="multiple level-0"):
        load_bom_csv(p)


def test_empty_data_raises(tmp_path):
    p = _write(tmp_path, "bad.csv", "level,part_number,quantity,revision\n")
    with pytest.raises(BomFormatError, match="no data"):
        load_bom_csv(p)
