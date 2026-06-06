# plm-changelens

**Deterministic BOM (bill of materials) diff with an optional AI layer that
drafts the change-impact and the requirement / test-spec updates — built for
regulated (medical-device) PLM change control.**

When a product's parts list changes, regulated industries must trace every
change through to the requirements, design and test documents it affects. Doing
that by hand is slow and error-prone. `plm-changelens` does the mechanical part
exactly, and lets an LLM draft the paperwork — keeping the safety-critical
computation deterministic and the writing assistive.

## Why this split matters

```
┌─ core/  (deterministic, no LLM, no network) ──────────────┐
│  Compare two BOM versions → exactly which parts were       │
│  added / removed / had quantity or revision changes,       │
│  with the hierarchical path of each change.                │
└────────────────────────────────────────────────────────────┘
            │  (a precise, hallucination-free change set)
            ▼
┌─ llm/  (optional, provider-swappable, off by default) ─────┐
│  Turn the change set into a plain-language impact summary   │
│  and DRAFT updates to the affected requirements / tests.    │
│  Every claim is traced back to a concrete change.           │
└────────────────────────────────────────────────────────────┘
```

The part that affects safety (what changed) never depends on a language model.
Only the writing assistance does — and the tool runs fully without it.

## Quick start (no install, no account, no card)

```bash
# deterministic diff, human-readable
PYTHONPATH=src python -m plm_changelens.cli diff examples/bom_old.csv examples/bom_new.csv

# machine-readable JSON
PYTHONPATH=src python -m plm_changelens.cli diff old.csv new.csv --format json
```

### BOM CSV format

| column | meaning |
|---|---|
| `level` | hierarchy level; the single `level=0` row is the top assembly |
| `part_number` | part identity |
| `quantity` | numeric quantity |
| `revision` | revision string (e.g. `A`, `01`) |

Extra columns (description, supplier, …) are preserved. Malformed input is
rejected with the offending row number — the tool never guesses.

## Design

- **Dependency-free runtime** (`dependencies = []`): the deterministic core uses
  only the standard library. New dependencies require an ADR.
- **Domain-agnostic core + domain pack**: `core/` (abstract tree diff) is reused
  via `packs/plm/` (BOM semantics), so the engine ports to other domains.
- **Provider-swappable LLM** via `LLM_PROVIDER` env var; defaults to local/free,
  tests use a deterministic mock (no network).

Architecture decisions: [`docs/adr/`](docs/adr/). Prior-art audit:
[`docs/adr/0001-prior-art-audit.md`](docs/adr/0001-prior-art-audit.md).

## Status

Phase 1 (deterministic core + CLI) is implemented and tested. The optional LLM
layer (impact summary, document drafts, traceability diff) is Phase 2.

## Limitations (honest disclosure)

- Input is a **generic CSV / intermediate format**. Direct connectors to
  commercial PLM systems (Windchill, Teamcenter, …) are out of scope; live data
  integration belongs to a deployment phase.
- The traceability output is an internal JSON model. Conformance to a specific
  regulatory submission format (ReqIF / IEC 62304 deliverables) is not yet
  guaranteed and would need a conversion layer.
- Tree-diff cost grows with BOM size; very large BOMs (thousands of nodes) may
  need the APTED variant (see ADR-0002).

## License

MIT — see [LICENSE](LICENSE).
