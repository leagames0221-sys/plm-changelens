"""Optional LLM layer.

Nothing in ``core`` or ``packs`` imports this package, so the deterministic
features run with the LLM layer entirely absent (R3.2). Providers are selected
at runtime via the ``LLM_PROVIDER`` environment variable (R7.2) and the default
is a deterministic, offline mock (no account, no network) (K-2/K-3).
"""
