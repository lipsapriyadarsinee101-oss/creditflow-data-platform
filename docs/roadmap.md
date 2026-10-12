# Engineering roadmap

This file tracks planned extensions; these capabilities are not implemented yet.

## Next iteration: operational reliability

- Add source-owned sequence numbers and conflict alerts.
- Define freshness SLOs and external alert routing.
- Execute integration tests on a dedicated Databricks synthetic-data schema.
- Add schema migration/version management.
- Enforce retention across raw data, exports, Delta history, and backups.

## Distributed platform expansion

- Add incremental source checkpoints and event-stream ingestion.
- Integrate dbt with the cloud silver product.
- Materialize only affected aggregate partitions for large datasets.
- Provision private endpoints, DNS, managed identities, and external locations.
- Replace development tokens with workload identity federation.
- Add fixed-decimal financial amounts and source reconciliations.

## Consumer experience

- Add authenticated product serving and freshness metadata.
- Add downstream contract checks and lineage event publication.
- Build a synthetic-only model-training example with validation, leakage checks, and model registry; do not present it as a lending decision system.
