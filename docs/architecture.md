# Architecture and engineering decisions

## Domain and products

The grain of silver is one application. Each event carries a source-owned application ID and timezone-aware version timestamp. Events can be repeated or arrive out of order. A customer can own multiple applications. Gold daily aggregates applications by application date and channel; approval volume excludes pending and rejected applications.

Gold features are illustrative transformations, not a credit-risk model. The principal-payment-to-income ratio excludes interest and fees, so it is not an affordability calculation. Neither feature exports nor the API expose customer IDs or tokens.

## ADR 001: Two execution paths

SQLite provides an inexpensive, fully executable demo using the Python standard library. Spark/Delta implements the corresponding large-scale batch processing shape. These are separate engines rather than a runtime abstraction pretending to make every SQL operation portable.

Shared input validation prevents most contract divergence. Their metrics differ: local accepted/rejected counters count physical input lines, while Spark deduplicates event hashes before counting. Local bronze hashing trims leading/trailing whitespace but preserves JSON field order, so semantically equivalent encodings can produce multiple bronze events. Silver selects one deterministic latest version.

## ADR 002: Event ordering

The authoritative order is normalized UTC timestamp, followed by descending SHA-256 event hash. Equal-time conflicts therefore converge regardless of input order. The hash tie-break does not establish business correctness: production sources should provide monotonic sequence/version IDs, and equal-version divergent payloads should alert the owning team.

Local input is streamed line by line to keep memory bounded. SQLite's application primary key supports keyed updates. Spark uses a window to pick a single candidate per application before MERGE, avoiding ambiguous multiple matches.

## ADR 003: Transaction boundary

Local bronze, quarantine, silver, and run metadata DML share one transaction. The quality gate rolls the entire batch back on failure; initial empty schema tables may remain. Spark's Delta transactions are per-table: bronze and quarantine survive a failed gate, while silver is unchanged. A failed Spark run after silver commit can be replayed to recreate gold views.

Neither engine claims distributed exactly-once delivery. The contract is replay-safe final state, under one active writer per domain. Airflow and Databricks job configurations enforce one active run; operators must avoid manually starting a second independent writer.

## ADR 004: Privacy and key management

HMAC-SHA256 avoids publishing raw customer IDs in silver. A stored SHA-256 key fingerprint catches accidental changes that would mix incompatible tokens. Use random high-entropy secret material outside this repository; demo keys are solely for synthetic data. Rotation is an explicit full rebuild of affected products.

Bronze retains raw source IDs. HMAC is pseudonymization, not anonymization. Production storage encryption, access audit, key controls, retention, deletion, and lawful processing require tenant-specific implementation.

## Performance and costs

The local benchmark records its own runtime rather than claiming external performance numbers. Spark caches validated rows only during the batch and unpersists in a finally block. Existing job compute avoids silently provisioning expensive clusters. Select worker sizes based on measured input volume; profile skew, shuffle, file sizes, and MERGE duration before optimizing. Do not partition by application ID or customer token.

Gold is a view to avoid repeated full writes. At larger scale, materialize daily aggregates with affected-partition recomputation and explicit late-event windows. The current example performs a full-source batch; watermark ingestion and source checkpoints are future work.
