"""R2.2/R2.3: BOM diff classification into the four categories + path."""

from __future__ import annotations

from pathlib import Path

from plm_changelens.core.change_model import ChangeCategory
from plm_changelens.packs.plm.bom_loader import load_bom_csv
from plm_changelens.packs.plm.classify import diff_boms

FIX = Path(__file__).parent / "fixtures"


def _run():
    old = load_bom_csv(FIX / "bom_old.csv")
    new = load_bom_csv(FIX / "bom_new.csv")
    return diff_boms(old, new)


def test_counts_match_expected():
    cs = _run()
    counts = cs.counts()
    assert counts["part_added"] == 1
    assert counts["part_removed"] == 1
    assert counts["quantity_changed"] == 1
    assert counts["revision_updated"] == 1


def test_added_part_is_washer_with_path():
    cs = _run()
    added = cs.by_category(ChangeCategory.PART_ADDED)
    assert [a.part_number for a in added] == ["PART-330"]
    assert added[0].path == ["ASSY-100", "SUB-210"]


def test_removed_part_is_cover():
    cs = _run()
    removed = cs.by_category(ChangeCategory.PART_REMOVED)
    assert [r.part_number for r in removed] == ["PART-110"]


def test_quantity_change_screw_4_to_6():
    cs = _run()
    q = cs.by_category(ChangeCategory.QUANTITY_CHANGED)
    assert len(q) == 1
    assert q[0].part_number == "PART-310"
    assert q[0].old["quantity"] == 4.0
    assert q[0].new["quantity"] == 6.0


def test_revision_update_bracket_b_to_c():
    cs = _run()
    r = cs.by_category(ChangeCategory.REVISION_UPDATED)
    assert len(r) == 1
    assert r[0].part_number == "PART-320"
    assert r[0].old["revision"] == "B"
    assert r[0].new["revision"] == "C"


def test_determinism_same_changeset_each_run():
    a = _run().to_dict()
    b = _run().to_dict()
    assert a == b


def test_sibling_reorder_is_not_a_change(tmp_path):
    """Re-sorting BOM rows (same parts) must NOT surface spurious add/remove."""
    from plm_changelens.packs.plm.bom_loader import load_bom_csv

    old = tmp_path / "old.csv"
    new = tmp_path / "new.csv"
    old.write_text(
        "level,part_number,quantity,revision\n0,TOP,1,A\n1,PART-A,1,A\n1,PART-B,1,A\n",
        encoding="utf-8",
    )
    new.write_text(
        "level,part_number,quantity,revision\n0,TOP,1,A\n1,PART-B,1,A\n1,PART-A,1,A\n",
        encoding="utf-8",
    )
    cs = diff_boms(load_bom_csv(old), load_bom_csv(new))
    assert sum(cs.counts().values()) == 0


def test_same_part_at_two_levels_change_is_localized(tmp_path):
    """A part number used at two levels: a change to one must not bleed to the other."""
    from plm_changelens.core.change_model import ChangeCategory
    from plm_changelens.packs.plm.bom_loader import load_bom_csv

    old = tmp_path / "old.csv"
    new = tmp_path / "new.csv"
    base = (
        "level,part_number,quantity,revision\n"
        "0,TOP,1,A\n1,COMMON,1,A\n1,SUB,1,A\n2,COMMON,1,{}\n"
    )
    old.write_text(base.format("A"), encoding="utf-8")
    new.write_text(base.format("B"), encoding="utf-8")  # only the deep COMMON changes
    cs = diff_boms(load_bom_csv(old), load_bom_csv(new))
    rev = cs.by_category(ChangeCategory.REVISION_UPDATED)
    assert len(rev) == 1
    assert rev[0].path == ["TOP", "SUB"]  # localized to the nested instance only


def _mk(tmp_path, name, body_rows):
    p = tmp_path / name
    p.write_text(
        "level,part_number,quantity,revision\n" + "\n".join(body_rows) + "\n",
        encoding="utf-8",
    )
    return p


def test_simultaneous_quantity_and_revision_change_yields_two_items(tmp_path):
    old = _mk(tmp_path, "o.csv", ["0,TOP,1,A", "1,P,2,A"])
    new = _mk(tmp_path, "n.csv", ["0,TOP,1,A", "1,P,5,C"])
    cs = diff_boms(load_bom_csv(old), load_bom_csv(new))
    assert cs.counts()["quantity_changed"] == 1
    assert cs.counts()["revision_updated"] == 1


def test_fractional_quantity_is_preserved_as_float(tmp_path):
    old = _mk(tmp_path, "o.csv", ["0,TOP,1,A", "1,WIRE,0.5,A"])
    new = _mk(tmp_path, "n.csv", ["0,TOP,1,A", "1,WIRE,1.5,A"])
    cs = diff_boms(load_bom_csv(old), load_bom_csv(new))
    q = cs.by_category(ChangeCategory.QUANTITY_CHANGED)[0]
    assert q.old["quantity"] == 0.5 and isinstance(q.old["quantity"], float)
    assert q.new["quantity"] == 1.5


def test_remove_all_children(tmp_path):
    old = _mk(tmp_path, "o.csv", ["0,TOP,1,A", "1,X,1,A", "1,Y,1,A"])
    new = _mk(tmp_path, "n.csv", ["0,TOP,1,A"])
    cs = diff_boms(load_bom_csv(old), load_bom_csv(new))
    assert cs.counts()["part_removed"] == 2
    assert sum(cs.counts().values()) == 2
