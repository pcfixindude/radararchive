# Next Steps

## Phase 114 - Georef improvement (Draft)

Goal: Improve decoded overlay geographic placement for local prototype playback.

```bash
make test
make backend
make frontend
```

## Phase 113 verification commands

```bash
make test
make mrms-bulk-local-ingest ARGS='--real --limit 8'
# simulate recovery after partial ingest:
make mrms-bulk-local-ingest ARGS='--real --retry-failed'
make mrms-bulk-local-ingest ARGS='--real --limit 8 --warm-cache'
```

Local result after Phase 113:

- Ingest report uses `success` / `partial_success` / `failed` statuses
- Transient download failures retry with bounded attempts
- `--retry-failed` retries only failed frames from latest report
- `--repair` re-downloads empty or checksum-mismatched raw files
- `--missing-only` skips frames with valid local raw files
- Warm-cache still runs on `success` and `partial_success`

## Phase 112 verification commands

```bash
make test
cd frontend && npm test && npm run build
make mrms-bulk-local-ingest ARGS='--real --limit 8 --warm-cache'
```

## Phase 111 verification commands

```bash
make test
make mrms-warm-frame-cache
```
