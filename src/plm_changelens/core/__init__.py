"""Domain-agnostic deterministic core: tree model + tree-edit-distance diff.

This package knows nothing about BOMs or medical devices. It operates on
abstract labelled trees so it can be reused for any hierarchical-diff domain
(ADR-0002). No LLM, no network, no third-party runtime dependencies.
"""
