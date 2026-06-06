"""Command-line interface (R6).

Subcommands:
    diff    deterministic BOM diff (no LLM, no network)
    impact  LLM change-impact summary (optional layer; falls back to the diff)
    draft   LLM requirement/test-spec update drafts (optional layer)
    trace   deterministic traceability-table impact (no LLM)

The optional LLM layer is selected with --llm-provider / $LLM_PROVIDER (R6.2,
R7.2); the default provider is an offline deterministic mock.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .packs.plm.bom_loader import BomFormatError, load_bom_csv
from .packs.plm.classify import diff_boms
from .packs.plm.traceability import TraceFormatError, diff_traceability, load_trace_csv
from .report.human_report import render_human
from .report.json_report import render_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="plm-changelens",
        description="Deterministic BOM diff with an optional LLM change-impact layer.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    diff_p = sub.add_parser("diff", help="Diff two BOM CSV files (deterministic).")
    diff_p.add_argument("old")
    diff_p.add_argument("new")
    diff_p.add_argument("--format", choices=["human", "json"], default="human")
    diff_p.set_defaults(func=_cmd_diff)

    impact_p = sub.add_parser("impact", help="LLM change-impact summary (optional).")
    impact_p.add_argument("old")
    impact_p.add_argument("new")
    impact_p.add_argument("--llm-provider", default=None, help="mock|ollama|workers_ai")
    impact_p.set_defaults(func=_cmd_impact)

    draft_p = sub.add_parser("draft", help="LLM requirement/test draft generation.")
    draft_p.add_argument("old")
    draft_p.add_argument("new")
    draft_p.add_argument("--llm-provider", default=None, help="mock|ollama|workers_ai")
    draft_p.set_defaults(func=_cmd_draft)

    trace_p = sub.add_parser("trace", help="Traceability-table impact (deterministic).")
    trace_p.add_argument("old")
    trace_p.add_argument("new")
    trace_p.add_argument("trace_table", help="Trace-table CSV.")
    trace_p.set_defaults(func=_cmd_trace)

    return parser


def _load_pair(args) -> tuple:
    return load_bom_csv(args.old), load_bom_csv(args.new)


def _cmd_diff(args) -> int:
    try:
        old_root, new_root = _load_pair(args)
    except BomFormatError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    change_set = diff_boms(old_root, new_root)
    if args.format == "json":
        print(render_json(change_set))
    else:
        print(render_human(change_set), end="")
    return 0


def _cmd_impact(args) -> int:
    try:
        old_root, new_root = _load_pair(args)
    except BomFormatError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    change_set = diff_boms(old_root, new_root)

    from .llm.impact_summary import generate_impact_summary
    from .llm.provider import LLMUnavailableError, get_provider

    try:
        provider = get_provider(args.llm_provider)
        report = generate_impact_summary(change_set, provider)
    except LLMUnavailableError as exc:
        # R3.2: still deliver the deterministic change set if LLM is unavailable.
        print(f"warning: LLM layer unavailable ({exc}); emitting diff only.",
              file=sys.stderr)
        print(render_json(change_set))
        return 0
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    return 0


def _cmd_draft(args) -> int:
    try:
        old_root, new_root = _load_pair(args)
    except BomFormatError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    change_set = diff_boms(old_root, new_root)

    from .llm.doc_gen import generate_drafts
    from .llm.provider import LLMUnavailableError, get_provider

    try:
        provider = get_provider(args.llm_provider)
        bundle = generate_drafts(change_set, provider)
    except LLMUnavailableError as exc:
        print(f"warning: LLM layer unavailable ({exc}); emitting diff only.",
              file=sys.stderr)
        print(render_json(change_set))
        return 0
    print(json.dumps(bundle.to_dict(), indent=2, ensure_ascii=False))
    return 0


def _cmd_trace(args) -> int:
    try:
        old_root, new_root = _load_pair(args)
        links = load_trace_csv(args.trace_table)
    except (BomFormatError, TraceFormatError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    change_set = diff_boms(old_root, new_root)
    impact = diff_traceability(change_set, links)
    print(json.dumps(impact.to_dict(), indent=2, ensure_ascii=False))
    return 0


def _force_utf8_stdio() -> None:
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
