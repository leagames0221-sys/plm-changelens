# ADR-0001: Prior-art audit (decomposed reuse seeds)

- **Status**: Accepted
- **Date**: 2026-06-06

## Context

Before writing code we surveyed existing tools so we imitate proven cores
rather than inventing from scratch. A multi-source survey (25 claims, each
verified by independent adversarial review) found **no single tool** that does
"multi-level BOM structural diff → regulated change-impact document drafting".
The capability exists only as *separable* prior art per layer. This ADR fixes
what we reuse and what we build, so the synthesis is accountable.

## Decision

Reuse the following as **decomposed prior art** (patterns/algorithms/data-model
naming — not vendored code, to keep runtime dependencies empty, see ADR-0002):

| Layer | Prior art | What we imitate | License |
|---|---|---|---|
| BOM structural diff | zss (Zhang-Shasha) | 3 separated cost callbacks (insert/remove/update) + node alignment via recovered operations | BSD-3 |
| (alt) | APTED | state-of-the-art TED; fallback if zss perf insufficient | MIT |
| Diff output model | DeepDiff | named change categories + path representation (we specialise to BOM) | MIT |
| BOM attribute set | bom-diff | which attributes matter (qty / revision / ref-designator / supplier) | MIT |
| SDLC doc generation | spec-kit, cc-sdd | stage decomposition + EARS 5 templates + EARS→test-type mapping | MIT |
| Traceability model | Doorstop | per-item file + typed linkable object + link validation; VCS-native | BSD-3 |
| Traceability model | Sphinx-Needs | typed need objects; ISO 26262 / DO-178B/C adjacency to IEC 62304 | MIT |
| Traceability export | StrictDoc | multi-format export idea (we ship JSON first) | Apache-2.0 |
| Provider abstraction | LiteLLM / in-house ABC | provider ABC + env swap + mock fallback | MIT |

**What is genuinely ours (no prior art):** the integration layer — BOM diff
output → traceability-artifact update → LLM impact summary — and the medical /
PLM change-control framing.

## Consequences

- The tool's novelty is the *synthesis*, which is a portfolio strength.
- Each adopted idea is re-implemented in-house (dependency-zero), so no
  third-party supply-chain exposure from these seeds.

## Alternatives considered

- Adopt a single end-to-end tool — none exists (survey result).
- Vendor the libraries directly — rejected to keep `dependencies = []`
  (ADR-0002); we take the algorithm/pattern, not the package.

## Source

The full prior-art survey (each adopted seed cross-checked against its source)
is kept in private project notes and is not part of this repository.
