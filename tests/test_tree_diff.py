"""R2.1/R2.4: deterministic core tree-edit-distance + operation recovery."""

from __future__ import annotations

from plm_changelens.core.tree import Node
from plm_changelens.core.tree_diff import OpType, diff


def _leaf(label, payload=None):
    return Node(label=label, payload=payload)


def test_identical_trees_zero_distance_all_match():
    a = Node("R", children=[_leaf("x"), _leaf("y")])
    b = Node("R", children=[_leaf("x"), _leaf("y")])
    dist, ops = diff(a, b)
    assert dist == 0
    assert all(op.op is OpType.MATCH for op in ops)


def test_single_insert():
    a = Node("R", children=[_leaf("x")])
    b = Node("R", children=[_leaf("x"), _leaf("y")])
    dist, ops = diff(a, b)
    assert dist == 1
    assert sum(1 for op in ops if op.op is OpType.INSERT) == 1


def test_single_remove():
    a = Node("R", children=[_leaf("x"), _leaf("y")])
    b = Node("R", children=[_leaf("x")])
    dist, ops = diff(a, b)
    assert dist == 1
    assert sum(1 for op in ops if op.op is OpType.REMOVE) == 1


def test_relabel_is_update():
    a = Node("R", children=[_leaf("x")])
    b = Node("R", children=[_leaf("z")])
    dist, ops = diff(a, b)
    assert dist == 1
    assert sum(1 for op in ops if op.op is OpType.UPDATE) == 1


def test_determinism_repeated_runs_identical():
    a = Node("R", children=[_leaf("x"), Node("y", children=[_leaf("p")])])
    b = Node("R", children=[_leaf("x2"), Node("y", children=[_leaf("p"), _leaf("q")])])
    first = diff(a, b)
    for _ in range(5):
        again = diff(a, b)
        assert again[0] == first[0]
        assert [(o.op, getattr(o.a, "label", None), getattr(o.b, "label", None))
                for o in again[1]] == \
               [(o.op, getattr(o.a, "label", None), getattr(o.b, "label", None))
                for o in first[1]]
