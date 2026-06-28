"""Operator runbook guidance mapping from validation alert causes (review aids only)."""

from __future__ import annotations

from typing import Any, Optional

from backend.app.services.mrms_proof_bundle_diff import DIFF_MIXED, DIFF_WORSENED
from backend.app.services.validation_alerts import (
    CAUSE_CATALOG_GATE_MISSING,
    CAUSE_DECODER_UNAVAILABLE,
    CAUSE_NO_GRIB2_ARTIFACT,
    CAUSE_NO_NETWORK,
    CAUSE_PRODUCTION_FLAG_OFF,
    CAUSE_PROOF_BUNDLE_DIFF_WORSENED,
    CAUSE_PROOF_REGRESSION,
    CAUSE_UNKNOWN,
    CAUSE_ZERO_TILES_WRITTEN,
    SUGGESTED_ACTIONS,
)

RUNBOOK_PATH = "docs/RUNBOOK_REAL_MRMS_VALIDATION.md"
VERIFIED_CRITERIA_PATH = "docs/VERIFIED_MRMS_CRITERIA.md"
SIGNOFF_TEMPLATE_PATH = "docs/MRMS_OPERATOR_SIGNOFF_TEMPLATE.md"

GUIDANCE_BY_CAUSE: dict[str, dict[str, str]] = {
    "proof_bundle_diff_worsened": {
        "title": "Proof bundle diff worsened",
        "path": RUNBOOK_PATH,
        "anchor": "proof-bundle-diff-worsened",
        "section_label": "Proof bundle diff worsened",
    },
    "proof_bundle_diff_mixed": {
        "title": "Proof bundle diff mixed",
        "path": RUNBOOK_PATH,
        "anchor": "proof-bundle-diff-mixed",
        "section_label": "Proof bundle diff mixed",
    },
    CAUSE_PROOF_BUNDLE_DIFF_WORSENED: {
        "title": "Proof bundle diff operator review",
        "path": RUNBOOK_PATH,
        "anchor": "proof-bundle-diff-worsened",
        "section_label": "Proof bundle diff worsened",
    },
    CAUSE_PROOF_REGRESSION: {
        "title": "Proof regression",
        "path": RUNBOOK_PATH,
        "anchor": "proof-regression-and-sign-off-phase-27",
        "section_label": "Proof regression and sign-off",
    },
    CAUSE_DECODER_UNAVAILABLE: {
        "title": "No decoder available",
        "path": RUNBOOK_PATH,
        "anchor": "no-decoder-available",
        "section_label": "No decoder available",
    },
    CAUSE_ZERO_TILES_WRITTEN: {
        "title": "Zero tiles written",
        "path": RUNBOOK_PATH,
        "anchor": "zero-tiles-written",
        "section_label": "Zero tiles written",
    },
    CAUSE_PRODUCTION_FLAG_OFF: {
        "title": "Production flag off",
        "path": RUNBOOK_PATH,
        "anchor": "production-flag-off",
        "section_label": "Production flag off",
    },
    CAUSE_CATALOG_GATE_MISSING: {
        "title": "Catalog gate missing",
        "path": RUNBOOK_PATH,
        "anchor": "catalog-gate-missing",
        "section_label": "Catalog gate missing",
    },
    CAUSE_NO_NETWORK: {
        "title": "No network / stub mode",
        "path": RUNBOOK_PATH,
        "anchor": "common-failure-causes",
        "section_label": "Common failure causes",
    },
    CAUSE_NO_GRIB2_ARTIFACT: {
        "title": "No GRIB2 artifact",
        "path": RUNBOOK_PATH,
        "anchor": "common-failure-causes",
        "section_label": "Common failure causes",
    },
    CAUSE_UNKNOWN: {
        "title": "Validation troubleshooting",
        "path": RUNBOOK_PATH,
        "anchor": "check-recent-failures",
        "section_label": "Check recent failures",
    },
    "verified_mrms_criteria": {
        "title": "Verified MRMS criteria (not met)",
        "path": VERIFIED_CRITERIA_PATH,
        "anchor": "regression-and-sign-off-workflow-phase-27",
        "section_label": "Criteria overview",
    },
    "before_signoff": {
        "title": "What to do before sign-off",
        "path": RUNBOOK_PATH,
        "anchor": "what-to-do-before-sign-off",
        "section_label": "What to do before sign-off",
    },
}


def _guidance_item(cause: str, *, diff_status: Optional[str] = None) -> dict[str, Any]:
    meta = GUIDANCE_BY_CAUSE.get(cause, GUIDANCE_BY_CAUSE[CAUSE_UNKNOWN])
    suggested = SUGGESTED_ACTIONS.get(cause, SUGGESTED_ACTIONS.get(CAUSE_UNKNOWN, ""))
    if cause in ("proof_bundle_diff_worsened", "proof_bundle_diff_mixed", CAUSE_PROOF_BUNDLE_DIFF_WORSENED):
        if diff_status == DIFF_MIXED:
            meta = GUIDANCE_BY_CAUSE["proof_bundle_diff_mixed"]
            suggested = (
                "Review mixed proof bundle diff — some evidence improved and some worsened; "
                "see runbook section and re-run make scheduled-proof-bundle-handoff after fixes."
            )
        elif diff_status == DIFF_WORSENED:
            meta = GUIDANCE_BY_CAUSE["proof_bundle_diff_worsened"]
    return {
        "title": meta["title"],
        "path": meta["path"],
        "anchor": meta.get("anchor", ""),
        "section_label": meta.get("section_label", meta["title"]),
        "cause": cause,
        "suggested_action": suggested,
        "verified_mrms": False,
        "local_guidance_only": True,
        "prototype": True,
    }


def build_operator_guidance(alert: Optional[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build compact runbook guidance items from latest alert (review aids only)."""
    if alert is None or not alert.get("operator_attention_needed"):
        return []

    items: list[dict[str, Any]] = []
    seen_causes: set[str] = set()
    diff_status = alert.get("proof_bundle_diff_status")

    if alert.get("proof_bundle_diff_attention"):
        cause_key = CAUSE_PROOF_BUNDLE_DIFF_WORSENED
        if diff_status == DIFF_MIXED:
            cause_key = "proof_bundle_diff_mixed"
        elif diff_status == DIFF_WORSENED:
            cause_key = "proof_bundle_diff_worsened"
        if cause_key not in seen_causes:
            items.append(_guidance_item(cause_key, diff_status=diff_status))
            seen_causes.add(cause_key)

    for grouped in alert.get("grouped_failure_causes") or []:
        cause = str(grouped.get("cause") or CAUSE_UNKNOWN)
        if cause in seen_causes:
            continue
        if cause in GUIDANCE_BY_CAUSE or cause in SUGGESTED_ACTIONS:
            items.append(_guidance_item(cause))
            seen_causes.add(cause)

    if alert.get("operator_attention_needed"):
        for extra in ("verified_mrms_criteria", "before_signoff"):
            if extra not in seen_causes:
                items.append(_guidance_item(extra))
                seen_causes.add(extra)

    return items[:10]


def compact_operator_guidance(alert: Optional[dict[str, Any]]) -> list[dict[str, Any]]:
    return build_operator_guidance(alert)
