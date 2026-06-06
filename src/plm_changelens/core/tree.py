"""Abstract labelled-tree model for the deterministic diff core.

A ``Node`` carries an opaque ``label`` (used for matching/cost decisions) and
an ordered list of children. The diff algorithm (``tree_diff``) accesses
children only through ``get_children`` so any domain tree (e.g. a BOM) can be
adapted without the core depending on that domain. (ADR-0002)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Node:
    """A node in an ordered labelled tree.

    Attributes:
        label: Opaque comparison key. Two nodes are considered the *same
            identity* when their labels are equal; cost callbacks may inspect
            ``payload`` for finer-grained (e.g. quantity/revision) comparison.
        payload: Arbitrary domain data attached to the node (never inspected by
            the core except via caller-supplied cost callbacks).
        children: Ordered child nodes.
    """

    label: Any
    payload: Any = None
    children: list[Node] = field(default_factory=list)

    def add(self, child: Node) -> Node:
        self.children.append(child)
        return child


def get_children(node: Node) -> list[Node]:
    """Accessor used by the diff algorithm (keeps the core domain-agnostic)."""
    return node.children


def iter_postorder(node: Node):
    """Yield nodes in left-to-right post-order (children before parent)."""
    for child in node.children:
        yield from iter_postorder(child)
    yield node


def size(node: Node) -> int:
    """Total node count of the subtree rooted at ``node``."""
    return 1 + sum(size(c) for c in node.children)
