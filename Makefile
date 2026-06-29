.PHONY: setup backend frontend test lint dev seed db-reset collect-once process-once discover-mrms download-mrms inspect-grib2 decode-grib2 build-tile-cache build-production-tiles render-status render-queue-status enqueue-render-job render-worker-once render-worker validate-real-mrms validate-real-mrms-batch benchmark-real-mrms benchmark-render-queue scheduled-validation scheduled-proof-bundle scheduled-proof-bundle-handoff scheduled-proof-bundle-notify scheduled-proof-bundle-digest scheduled-proof-bundle-review-export scheduled-proof-bundle-operator-status scheduled-proof-bundle-visual-review validation-failures validation-alerts mrms-proof-report mrms-proof-regression mrms-signoff mrms-review-session mrms-review-sessions mrms-review-session-compare mrms-review-session-export mrms-review-session-exports mrms-proof-history mrms-proof-bundle mrms-proof-bundle-diff mrms-operator-handoff proof-bundle-diff-alert-history proof-bundle-diff-alert-trend proof-bundle-diff-escalation proof-bundle-diff-escalation-history proof-bundle-diff-escalation-metrics proof-bundle-diff-escalation-digest proof-bundle-diff-escalation-digest-history proof-bundle-diff-escalation-digest-diff proof-bundle-diff-acknowledge real-mrms-smoke-test catalog-status operator-review-status operator-workflow-presets mrms-visual-review mrms-visual-review-history mrms-visual-review-compare mrms-visual-review-comparison-history mrms-visual-review-hint mrms-visual-review-sample-set mrms-visual-review-readiness mrms-render-candidate-preflight mrms-render-candidate-dry-run-plan

ARGS ?=

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -U pip
	. .venv/bin/activate && pip install fastapi uvicorn pydantic pydantic-settings sqlalchemy pytest httpx python-dotenv
	cd frontend && npm install

backend:
	. .venv/bin/activate && uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

frontend:
	cd frontend && npm run dev

test:
	. .venv/bin/activate && pytest backend/tests -v

lint:
	. .venv/bin/activate && python -m compileall backend scripts

seed:
	. .venv/bin/activate && PYTHONPATH=. python scripts/seed_demo_data.py

db-reset:
	. .venv/bin/activate && PYTHONPATH=. python scripts/db_reset.py

collect-once:
	. .venv/bin/activate && PYTHONPATH=. python scripts/collect_once.py

process-once:
	. .venv/bin/activate && PYTHONPATH=. python scripts/process_once.py

discover-mrms:
	. .venv/bin/activate && PYTHONPATH=. python scripts/discover_mrms.py

download-mrms:
	. .venv/bin/activate && PYTHONPATH=. python scripts/download_mrms.py

inspect-grib2:
	. .venv/bin/activate && PYTHONPATH=. python scripts/inspect_grib2.py --latest-mrms --limit 1

decode-grib2:
	. .venv/bin/activate && PYTHONPATH=. python scripts/decode_grib2.py --latest-mrms --limit 1

build-tile-cache:
	. .venv/bin/activate && PYTHONPATH=. python scripts/build_tile_cache.py

build-production-tiles:
	. .venv/bin/activate && PYTHONPATH=. python scripts/build_production_tiles.py $(ARGS)

render-status:
	. .venv/bin/activate && PYTHONPATH=. python scripts/render_status.py

enqueue-render-job:
	. .venv/bin/activate && PYTHONPATH=. python scripts/enqueue_render_job.py $(ARGS)

render-worker-once:
	. .venv/bin/activate && PYTHONPATH=. python scripts/run_render_worker.py --once $(ARGS)

render-worker:
	. .venv/bin/activate && PYTHONPATH=. python scripts/run_render_worker.py $(ARGS)

render-queue-status:
	. .venv/bin/activate && PYTHONPATH=. python scripts/render_queue_status.py $(ARGS)

validate-real-mrms:
	. .venv/bin/activate && PYTHONPATH=. python scripts/validate_real_mrms.py $(ARGS)

validate-real-mrms-batch:
	. .venv/bin/activate && PYTHONPATH=. python scripts/batch_validate_mrms.py $(ARGS)

benchmark-real-mrms:
	. .venv/bin/activate && PYTHONPATH=. python scripts/benchmark_real_mrms.py $(ARGS)

benchmark-render-queue:
	. .venv/bin/activate && PYTHONPATH=. python scripts/benchmark_render_queue.py $(ARGS)

scheduled-validation:
	. .venv/bin/activate && PYTHONPATH=. python scripts/run_scheduled_validation.py $(ARGS)

scheduled-proof-bundle:
	. .venv/bin/activate && PYTHONPATH=. python scripts/run_scheduled_validation.py --proof --bundle --diff-bundle $(ARGS)

scheduled-proof-bundle-handoff:
	. .venv/bin/activate && PYTHONPATH=. python scripts/run_scheduled_validation.py --proof --bundle --diff-bundle --handoff $(ARGS)

scheduled-proof-bundle-notify:
	. .venv/bin/activate && PYTHONPATH=. python scripts/run_scheduled_validation.py --proof --bundle --diff-bundle --handoff --notify-stdout $(ARGS)

scheduled-proof-bundle-digest:
	. .venv/bin/activate && PYTHONPATH=. python scripts/run_scheduled_validation.py --proof --bundle --diff-bundle --handoff --digest $(ARGS)

scheduled-proof-bundle-review-export:
	. .venv/bin/activate && PYTHONPATH=. python scripts/run_scheduled_validation.py --proof --bundle --diff-bundle --handoff --digest --review-export $(ARGS)

scheduled-proof-bundle-operator-status:
	. .venv/bin/activate && PYTHONPATH=. python scripts/run_scheduled_validation.py --proof --bundle --diff-bundle --handoff --digest --review-export --operator-status $(ARGS)

scheduled-proof-bundle-visual-review:
	. .venv/bin/activate && PYTHONPATH=. python scripts/run_scheduled_validation.py --proof --bundle --diff-bundle --handoff --digest --review-export --operator-status --visual-review $(ARGS)

validation-failures:
	. .venv/bin/activate && PYTHONPATH=. python scripts/validation_failures.py $(ARGS)

validation-alerts:
	. .venv/bin/activate && PYTHONPATH=. python scripts/validation_alerts.py $(ARGS)

mrms-proof-report:
	. .venv/bin/activate && PYTHONPATH=. python scripts/generate_mrms_proof_report.py $(ARGS)

mrms-proof-regression:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_proof_regression.py $(ARGS)

mrms-signoff:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_signoff.py $(ARGS)

mrms-review-session:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_review_session.py $(ARGS)

mrms-review-sessions:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_review_sessions.py $(ARGS)

mrms-review-session-compare:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_review_session_compare.py $(ARGS)

mrms-review-session-export:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_review_session_export.py $(ARGS)

mrms-review-session-exports:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_review_session_exports.py $(ARGS)

mrms-review-session-export-diff:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_review_session_export_diff.py $(ARGS)

mrms-review-session-export-diff-history:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_review_session_export_diff.py --history $(ARGS)

mrms-review-session-export-diff-trend:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_review_session_export_diff_trend.py $(ARGS)

mrms-review-session-export-diff-trend-hint:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_review_session_export_diff_trend_hint.py $(ARGS)

operator-review-status:
	. .venv/bin/activate && PYTHONPATH=. python scripts/operator_review_status.py $(ARGS)

operator-workflow-presets:
	. .venv/bin/activate && PYTHONPATH=. python scripts/operator_workflow_presets.py $(ARGS)

mrms-visual-review:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_visual_review.py $(ARGS)

mrms-visual-review-history:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_visual_review.py --history $(ARGS)

mrms-visual-review-compare:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_visual_review_compare.py $(ARGS)

mrms-visual-review-comparison-history:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_visual_review_compare.py --history $(ARGS)

mrms-visual-review-hint:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_visual_review_hint.py $(ARGS)

mrms-visual-review-sample-set:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_visual_review_sample_set.py $(ARGS)

mrms-visual-review-readiness:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_visual_review_sample_readiness.py $(ARGS)

mrms-render-candidate-preflight:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_render_candidate_preflight.py $(ARGS)

mrms-render-candidate-dry-run-plan:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_render_candidate_dry_run_plan.py $(ARGS)

mrms-render-candidate-scaffold:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_render_candidate_scaffold.py $(ARGS)

mrms-render-candidate-sandbox:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_render_candidate_sandbox.py $(ARGS)

mrms-render-candidate-sandbox-export:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_render_candidate_sandbox_import_export.py --export $(ARGS)

mrms-render-candidate-sandbox-import-export:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_render_candidate_sandbox_import_export.py --export --import $(ARGS)

mrms-proof-history:
	. .venv/bin/activate && PYTHONPATH=. python scripts/mrms_proof_history.py $(ARGS)

mrms-proof-bundle:
	. .venv/bin/activate && PYTHONPATH=. python scripts/export_mrms_proof_bundle.py $(ARGS)

mrms-proof-bundle-diff:
	. .venv/bin/activate && PYTHONPATH=. python scripts/diff_mrms_proof_bundles.py $(ARGS)

mrms-operator-handoff:
	. .venv/bin/activate && PYTHONPATH=. python scripts/generate_operator_handoff.py $(ARGS)

proof-bundle-diff-alert-history:
	. .venv/bin/activate && PYTHONPATH=. python scripts/proof_bundle_diff_alert_history.py $(ARGS)

proof-bundle-diff-alert-trend:
	. .venv/bin/activate && PYTHONPATH=. python scripts/proof_bundle_diff_alert_trend.py $(ARGS)

proof-bundle-diff-escalation:
	. .venv/bin/activate && PYTHONPATH=. python scripts/proof_bundle_diff_escalation.py $(ARGS)

proof-bundle-diff-escalation-history:
	. .venv/bin/activate && PYTHONPATH=. python scripts/proof_bundle_diff_escalation_history.py $(ARGS)

proof-bundle-diff-escalation-metrics:
	. .venv/bin/activate && PYTHONPATH=. python scripts/proof_bundle_diff_escalation_metrics.py $(ARGS)

proof-bundle-diff-escalation-digest:
	. .venv/bin/activate && PYTHONPATH=. python scripts/proof_bundle_diff_escalation_digest.py $(ARGS)

proof-bundle-diff-escalation-digest-history:
	. .venv/bin/activate && PYTHONPATH=. python scripts/proof_bundle_diff_escalation_digest_history.py $(ARGS)

proof-bundle-diff-escalation-digest-diff:
	. .venv/bin/activate && PYTHONPATH=. python scripts/proof_bundle_diff_escalation_digest_diff.py $(ARGS)

proof-bundle-diff-acknowledge:
	. .venv/bin/activate && PYTHONPATH=. python scripts/proof_bundle_diff_acknowledgment.py $(ARGS)

real-mrms-smoke-test:
	. .venv/bin/activate && PYTHONPATH=. python scripts/real_mrms_smoke_test.py $(ARGS)

catalog-status:
	. .venv/bin/activate && PYTHONPATH=. python scripts/catalog_status.py $(ARGS)
