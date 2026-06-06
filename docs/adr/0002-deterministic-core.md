# ADR-0002: Zhang-Shasha deterministic core, implemented in-house

- **Status**: Accepted
- **Date**: 2026-06-06

## Context

A BOM is a multi-level ordered tree. The diff must report additions, removals,
quantity changes and revision updates **with structural correspondence** (which
part, under which parent). Because the result feeds regulated change control, it
must be deterministic and free of model hallucination. It must also run on a
consumer laptop with no setup friction.

## Decision

Implement the **Zhang-Shasha** ordered tree-edit-distance algorithm directly
(`core/tree_diff.py`) with three *separated* cost callbacks and full edit-
operation recovery (REMOVE / INSERT / UPDATE / MATCH). Keep the core
**domain-agnostic** (`core/` knows nothing about BOMs) and **dependency-free**
(standard library only). The PLM pack supplies BOM-semantic costs on top
(`packs/plm/bom_node.py`): a part-number mismatch is priced above remove+insert
so unrelated parts are never aligned as an "update".

## Consequences

- Pure-Python, deterministic, reproducible (same input → same operations),
  trivially unit-testable (no network, no model).
- `dependencies = []` preserved (minimum supply-chain exposure).
- If trees exceed a few thousand nodes and performance bites, revisit with APTED
  (a follow-up ADR), without changing the public `diff()` contract.

## Alternatives considered

- Vendor the `zss` package — adds a runtime dependency; rejected (we reuse the
  algorithm, ADR-0001).
- Naive recursive child-by-child compare (bom-diff style) — loses structural
  correspondence on reordered / re-parented subtrees; rejected.
- DeepDiff generic recursive diff — not tree-aware for hierarchy; used only as a
  naming-convention reference for the output model.
