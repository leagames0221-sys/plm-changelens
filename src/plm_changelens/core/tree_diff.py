"""Zhang-Shasha ordered tree-edit-distance with edit-operation recovery.

Implemented from the algorithm (Zhang & Shasha, 1989) rather than vendored, to
keep the runtime dependency set empty (ADR-0002). The public ``diff`` function
accepts three *separate* cost callbacks so a domain layer can assign different
semantic costs to insert / remove / update and inspect node payloads (e.g. to
tell a quantity change apart from a revision change). It returns both the scalar
distance and the list of edit operations (the node alignment), not just a number.

References:
    Zhang, K., & Shasha, D. (1989). Simple fast algorithms for the editing
    distance between trees and related problems. SIAM J. Comput. 18(6).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from .tree import Node, iter_postorder


class OpType(StrEnum):
    REMOVE = "remove"  # node present in A, absent in B
    INSERT = "insert"  # node present in B, absent in A
    UPDATE = "update"  # node in A maps to node in B, label/payload differ
    MATCH = "match"    # node in A maps to node in B, no change


@dataclass(frozen=True)
class Operation:
    op: OpType
    a: Node | None  # source node (None for INSERT)
    b: Node | None  # target node (None for REMOVE)


CostFn = Callable[[Node], float]
UpdateFn = Callable[[Node, Node], float]


def _default_insert(_n: Node) -> float:
    return 1.0


def _default_remove(_n: Node) -> float:
    return 1.0


def _default_update(a: Node, b: Node) -> float:
    return 0.0 if a.label == b.label else 1.0


def _annotate(root: Node):
    """Return (postorder_nodes, leftmost-leaf array, keyroots) — all 1-indexed."""
    post = list(iter_postorder(root))
    index = {id(n): i for i, n in enumerate(post, start=1)}
    n = len(post)
    lmld = [0] * (n + 1)  # leftmost-leaf-descendant postorder index, 1-based
    for i, node in enumerate(post, start=1):
        if not node.children:
            lmld[i] = i
        else:
            lmld[i] = lmld[index[id(node.children[0])]]
    seen: set[int] = set()
    keyroots: list[int] = []
    for i in range(n, 0, -1):
        if lmld[i] not in seen:
            seen.add(lmld[i])
            keyroots.append(i)
    keyroots.sort()
    return post, lmld, keyroots


def diff(
    a_root: Node,
    b_root: Node,
    insert_cost: CostFn = _default_insert,
    remove_cost: CostFn = _default_remove,
    update_cost: UpdateFn = _default_update,
) -> tuple[float, list[Operation]]:
    """Compute the tree-edit distance and recovered edit operations.

    Args:
        a_root: root of the source tree (old version).
        b_root: root of the target tree (new version).
        insert_cost: cost to insert a (target) node; receives the node.
        remove_cost: cost to remove a (source) node; receives the node.
        update_cost: cost to relabel a -> b; receives both nodes. Return 0 to
            signal an exact match (emitted as a MATCH operation).

    Returns:
        (distance, operations). ``operations`` is deterministic for a given
        input (stable tie-breaking: remove < insert < update/match).
    """
    a_post, a_lmld, a_keyroots = _annotate(a_root)
    b_post, b_lmld, b_keyroots = _annotate(b_root)
    m, n = len(a_post), len(b_post)

    # Full-subtree results, indexed by 1-based postorder ids.
    treedist = [[0.0] * (n + 1) for _ in range(m + 1)]
    treeops: list[list[list[Operation]]] = [
        [[] for _ in range(n + 1)] for _ in range(m + 1)
    ]

    for i in a_keyroots:
        for j in b_keyroots:
            _forest_dist(
                i, j, a_post, b_post, a_lmld, b_lmld,
                treedist, treeops, insert_cost, remove_cost, update_cost,
            )
    return treedist[m][n], treeops[m][n]


def _forest_dist(
    i, j, a_post, b_post, a_lmld, b_lmld,
    treedist, treeops, insert_cost, remove_cost, update_cost,
) -> None:
    ioff = a_lmld[i] - 1
    joff = b_lmld[j] - 1
    p = i - ioff  # number of source nodes in this forest
    q = j - joff  # number of target nodes in this forest

    fd = [[0.0] * (q + 1) for _ in range(p + 1)]
    ops: list[list[list[Operation]]] = [[[] for _ in range(q + 1)] for _ in range(p + 1)]

    for x in range(1, p + 1):
        a_node = a_post[x + ioff - 1]
        fd[x][0] = fd[x - 1][0] + remove_cost(a_node)
        ops[x][0] = ops[x - 1][0] + [Operation(OpType.REMOVE, a_node, None)]
    for y in range(1, q + 1):
        b_node = b_post[y + joff - 1]
        fd[0][y] = fd[0][y - 1] + insert_cost(b_node)
        ops[0][y] = ops[0][y - 1] + [Operation(OpType.INSERT, None, b_node)]

    for x in range(1, p + 1):
        ax = x + ioff
        a_node = a_post[ax - 1]
        for y in range(1, q + 1):
            by = y + joff
            b_node = b_post[by - 1]

            cost_remove = fd[x - 1][y] + remove_cost(a_node)
            cost_insert = fd[x][y - 1] + insert_cost(b_node)

            if a_lmld[ax] == a_lmld[i] and b_lmld[by] == b_lmld[j]:
                # Both are simple subtrees relative to this keyroot pair.
                u = update_cost(a_node, b_node)
                cost_update = fd[x - 1][y - 1] + u
                best, chosen = _pick(cost_remove, cost_insert, cost_update)
                if chosen == "remove":
                    fd[x][y] = cost_remove
                    ops[x][y] = ops[x - 1][y] + [Operation(OpType.REMOVE, a_node, None)]
                elif chosen == "insert":
                    fd[x][y] = cost_insert
                    ops[x][y] = ops[x][y - 1] + [Operation(OpType.INSERT, None, b_node)]
                else:
                    fd[x][y] = cost_update
                    optype = OpType.MATCH if u == 0 else OpType.UPDATE
                    ops[x][y] = ops[x - 1][y - 1] + [Operation(optype, a_node, b_node)]
                treedist[ax][by] = fd[x][y]
                treeops[ax][by] = ops[x][y]
            else:
                pp = a_lmld[ax] - 1 - ioff
                qq = b_lmld[by] - 1 - joff
                cost_tree = fd[pp][qq] + treedist[ax][by]
                best, chosen = _pick(cost_remove, cost_insert, cost_tree)
                if chosen == "remove":
                    fd[x][y] = cost_remove
                    ops[x][y] = ops[x - 1][y] + [Operation(OpType.REMOVE, a_node, None)]
                elif chosen == "insert":
                    fd[x][y] = cost_insert
                    ops[x][y] = ops[x][y - 1] + [Operation(OpType.INSERT, None, b_node)]
                else:
                    fd[x][y] = cost_tree
                    ops[x][y] = ops[pp][qq] + treeops[ax][by]


def _pick(cost_remove: float, cost_insert: float, cost_third: float):
    """Deterministic argmin with fixed tie-break order: remove < insert < third."""
    best = cost_remove
    chosen = "remove"
    if cost_insert < best:
        best = cost_insert
        chosen = "insert"
    if cost_third < best:
        best = cost_third
        chosen = "third"
    return best, chosen
