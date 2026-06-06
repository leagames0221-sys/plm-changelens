# ADR-0004: Lightweight internal traceability model

- **Status**: Accepted
- **Date**: 2026-06-06

## Context

We need to tell which requirement<->design<->test links a BOM change affects, and
which newly added parts still lack a link (R5). Medical-device software is
adjacent to IEC 62304 traceability practice. We must avoid heavy framework
dependencies and keep the output diff-able and deterministic.

## Decision

Model a traceability table as a list of typed, validatable links
(`requirement_id`, `design_id`, `test_id`, covered `part_numbers`) — borrowing
Doorstop's per-item, link-validation idea and Sphinx-Needs' typed-object idea,
but as a light in-house structure (ADR-0001). Input is a simple CSV; output is
JSON (`affected` links with triggering parts + reasons, and `new_link_candidates`
for added parts). The computation is deterministic and uses no LLM.

## Consequences

- Plain CSV in / JSON out: VCS-friendly and easy to integrate.
- No dependency on Sphinx or a requirements framework.
- Regulatory submission formats (ReqIF, IEC 62304 deliverables) are **not**
  produced yet; a conversion/export layer is future work (documented as a
  limitation in the README).

## Alternatives considered

- Adopt Sphinx-Needs wholesale — pulls in Sphinx; rejected for v1.
- Adopt StrictDoc `.sdoc` directly — external dependency; we reuse only its
  multi-format-export idea (JSON first).
