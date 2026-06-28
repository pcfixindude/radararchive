"""Refresh local MRMS visual review sample readiness summary (advisory only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_visual_review_sample_readiness import (
    SUGGESTED_READINESS_COMMAND,
    SampleAnnotationValidationError,
    STATUS_ACCEPTABLE,
    STATUS_QUESTIONABLE,
    STATUS_REJECTED,
    STATUS_UNREVIEWED,
    build_visual_review_sample_readiness_payload,
    refresh_visual_review_sample_readiness,
    upsert_sample_annotation,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute local MRMS visual review sample readiness (Phase 61 — advisory only)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Persist readiness Markdown and update annotations JSON",
    )
    parser.add_argument("--sample-key", type=str, default="", help="Annotate one sample by key")
    parser.add_argument(
        "--status",
        type=str,
        default=STATUS_UNREVIEWED,
        choices=[
            STATUS_UNREVIEWED,
            STATUS_ACCEPTABLE,
            STATUS_QUESTIONABLE,
            STATUS_REJECTED,
        ],
        help="Annotation status when using --sample-key",
    )
    parser.add_argument("--notes", type=str, default="", help="Operator notes for annotation")
    parser.add_argument("--reviewer", type=str, default="", help="Reviewer label for annotation")
    parser.add_argument(
        "--tags",
        type=str,
        default="",
        help="Comma-separated issue tags for annotation",
    )
    args = parser.parse_args()

    print(
        "WARNING: Visual review sample readiness is local advisory guidance only — NOT verified MRMS. "
        "candidate_ready is NOT production authorization. Does not clear alerts or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)

    if args.sample_key:
        try:
            record = upsert_sample_annotation(
                storage,
                sample_key=args.sample_key,
                status=args.status,
                operator_notes=args.notes or None,
                reviewer_label=args.reviewer or None,
                issue_tags=[tag.strip() for tag in args.tags.split(",") if tag.strip()],
            )
        except SampleAnnotationValidationError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        if args.json_report:
            print(json.dumps(record, indent=2, sort_keys=True))
            return
        print(f"Annotation saved for {record.get('sample_key')} — status={record.get('status')}")
        return

    if args.refresh:
        readiness = refresh_visual_review_sample_readiness(storage)
    else:
        readiness = build_visual_review_sample_readiness_payload(storage)["readiness"]

    if args.json_report:
        print(json.dumps(readiness, indent=2, sort_keys=True))
        return

    print("MRMS visual review sample readiness (local advisory only — NOT verified MRMS):")
    print(f"  readiness_level: {readiness.get('readiness_level')}")
    print(f"  readiness_reason: {readiness.get('readiness_reason')}")
    print(f"  total_selected_samples: {readiness.get('total_selected_samples')}")
    print(f"  reviewed_samples: {readiness.get('reviewed_samples')}")
    print(f"  unreviewed_samples: {readiness.get('unreviewed_samples')}")
    print(f"  acceptable_count: {readiness.get('acceptable_count')}")
    print(f"  questionable_count: {readiness.get('questionable_count')}")
    print(f"  rejected_count: {readiness.get('rejected_count')}")
    print(f"  missing_artifact_samples: {readiness.get('missing_artifact_samples')}")
    print(f"  stale_samples: {readiness.get('stale_samples')}")
    print(f"  markdown_path: {readiness.get('markdown_path')}")
    print(f"  annotations_path: {readiness.get('annotations_path')}")
    print(f"  suggested_command: {readiness.get('suggested_command') or SUGGESTED_READINESS_COMMAND}")
    print(f"  verified_mrms: {readiness.get('verified_mrms')}")


if __name__ == "__main__":
    main()
