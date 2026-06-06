#!/usr/bin/env bash
# Layer 4 manual sweep: block PRIVATE / internal artifacts from reaching the
# tracked tree before a push or a PUBLIC flip. Greps tracked files for paths and
# markers that must never appear in this repository.
set -euo pipefail

fail=0

# 1. No private directories should ever be tracked (only .claude/settings.json
#    is allowed under .claude/).
if git ls-files | grep -E '(^|/)\.claude/(?!settings\.json)|(^|/)private/' >/dev/null 2>&1; then
  echo "ERROR: a private path is tracked by git:" >&2
  git ls-files | grep -E '(^|/)\.claude/|(^|/)private/' >&2 || true
  fail=1
fi

# 2. No secret material in tracked text.
#    (Project-specific customer/internal term lists are kept OUT of this public
#    repo; run them from a private sweep list before a visibility flip.)
markers='BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}|-----BEGIN'
if git grep -I -n -E "$markers" -- ':!scripts/private_path_check.sh' >/dev/null 2>&1; then
  echo "ERROR: internal marker found in tracked files:" >&2
  git grep -I -n -E "$markers" -- ':!scripts/private_path_check.sh' >&2 || true
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "private_path_check FAILED" >&2
  exit 1
fi
echo "private_path_check OK"
