# Operations runbook

## Successful daily batch

1. Supply source JSONL at the configured persistent location.
2. Run the ingest command or trigger the orchestrator.
3. Inspect accepted/rejected counts and changes; investigate unexpected zero input, rejection spikes, or volume changes.
4. Confirm gold totals reconcile to silver; publish exports.
5. Check the health endpoint and consumer availability.

The health endpoint verifies the database and reports the last successful run. It does not implement a freshness SLO. A production monitor should compare that timestamp against a defined daily deadline and alert via the team's chosen system.

## Quality gate failure

Local mode: transaction is rolled back, so source input remains the diagnostic source. Quarantine written in that failed batch is also rolled back. Fix source records or investigate the contract before retrying. To inspect a controlled synthetic failure, explicitly relax the threshold to retain quarantined rows.

Spark mode: inspect bronze and quarantine; silver is unchanged when the gate fails. Repair or replace the source, then rerun. Never lower the threshold for real data solely to make a job green.

## Replay and backfill

Re-run the same input for recovery. Silver converges on the latest version; local replay reports zero changed rows. Backfill by supplying historical files, retaining their original event timestamps. Do not replace timestamps with processing time, or old versions may overwrite current data.

## Key mismatch

Stop ingestion. Restore the original secret or perform an approved full rebuild in a new database/schema using the new key. Validate consumer joins before switching consumers. Do not edit the stored fingerprint to bypass the guard.

## Recovery and rollback

Back up local databases after closing writers; use SQLite's backup API for a consistent online snapshot. Restore to a new path and reconcile counts before switching the API. On Delta, record table versions before deployments; use time travel or restore according to workspace retention policies, then rerun downstream views.

## Data retention and erasure

Retention values in `governance/products.json` are policy targets, not an active scheduler. Real deployment must cover bronze, quarantine, silver, exports, cloud logs, Delta history, and backups. Coordinate erasure with the source system so replay cannot recreate deleted records.

## Scale milestones

Measure p50/p95 runtime, input throughput, rejected fraction, freshness lag, and compute cost per accepted record. Add source watermarks/checkpoints, schema evolution reviews, partition-aware gold materialization, distributed integration tests, and authenticated API serving before production use.
