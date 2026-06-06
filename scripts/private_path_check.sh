#!/usr/bin/env bash
# Layer 4 manual sweep: block PRIVATE / internal artifacts from reaching the
# tracked tree before a push or a PUBLIC flip. Greps tracked files for paths and
# markers that must never appear in this repository.
set -euo pipefail

fail=0

# 1. No private directories should ever be tracked.
if git ls-files | grep -E '(^|/)\.claude/(?!settings\.json)|(^|/)(private|private|private)/' >/dev/null 2>&1; then
  echo "ERROR: a private path is tracked by git:" >&2
  git ls-files | grep -E '(^|/)\.claude/|(^|/)(private|private|private)/' >&2 || true
  fail=1
fi

# 2. No internal markers in tracked text.
#    (Add project-specific customer/internal terms to this list before a flip.)
markers='\.env|BEGIN [A-Z ]*PRIVATE KEY|redacted|redacted'
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
