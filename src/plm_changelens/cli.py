"""Command-line interface (R6).

Phase 1 exposes the deterministic ``diff`` subcommand, which runs with NO LLM
and NO network. The optional LLM layer (impact summary / doc drafts) is wired in
Phase 2 behind an explicit flag so the core stays usable on its own (R3.2).
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .packs.plm.bom_loader import BomFormatError, load_bom_csv
from .packs.plm.classify import diff_boms
from .report.human_report import render_human
from .report.json_report import render_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="plm-changelens",
        description=(
            "Deterministic BOM structural diff (with an optional LLM "
            "change-impact layer)."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    diff_p = sub.add_parser("diff", help="Diff two BOM CSV files (old vs new).")
    diff_p.add_argument("old", help="Path to the old/baseline BOM CSV.")
    diff_p.add_argument("new", help="Path to the new/revised BOM CSV.")
    diff_p.add_argument(
        "--format",
        choices=["human", "json"],
        default="human",
        help="Output format (default: human).",
    )
    diff_p.set_defaults(func=_cmd_diff)
    return parser


def _cmd_diff(args: argparse.Namespace) -> int:
    try:
        old_root = load_bom_csv(args.old)
        new_root = load_bom_csv(args.new)
    except BomFormatError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    change_set = diff_boms(old_root, new_root)
    if args.format == "json":
        print(render_json(change_set))
    else:
        print(render_human(change_set), end="")
    return 0


def _force_utf8_stdio() -> None:
    """Make output robust on non-UTF-8 consoles (e.g. Windows cp932)."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


def main(argv: list[str] | None = None) -> int:
    _force_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
