# ADR-0003: In-house LLM provider ABC + env swap, mock default

- **Status**: Accepted
- **Date**: 2026-06-06

## Context

The change-impact summary and document drafts need an LLM, but: (a) the tool
must run with no account / card / network by default (K-2/K-3); (b) tests must
be deterministic and offline; (c) the user wants to swap between local (Ollama),
free-tier hosted (Workers AI) and Copilot-class providers without code changes;
(d) we keep `dependencies = []`.

## Decision

A minimal in-house `LLMProvider` ABC with one method (`complete`). Concrete
providers are selected at runtime by `LLM_PROVIDER` (or `--llm-provider`). The
default is an **offline deterministic mock**, so nothing reaches the network
unless explicitly requested. Hosted providers (Ollama, Workers AI) use only
`urllib` from the standard library — no SDK, no new dependency. External
providers send data out only on explicit opt-in with user-supplied credentials
(R8.1).

## Consequences

- Deterministic, offline tests via the mock provider.
- Adding a provider = one subclass + one factory branch; no core change.
- The evidence linkage in the impact summary is structural (code-attached), so a
  weak/changed model cannot break traceability (R3.3).

## Alternatives considered

- LiteLLM central gateway — feature-rich but adds a runtime dependency and is
  overkill for v1; revisit via a future ADR if multi-provider routing is needed.
- Direct API calls inline — not swappable, not testable; rejected.
- Default to a real provider — would require setup/network on first run;
  rejected in favour of the mock default.
