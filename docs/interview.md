# Ten-minute interview walkthrough

1. **Business problem (1 min):** explain why repeated and late lending application events must produce consistent reporting and reusable data products.
2. **Architecture (1 min):** trace source → bronze → validation → silver → gold. State the grain and owner of each product.
3. **Live local demo (2 min):** generate 10,000 events, run twice, explain why the second run has zero changes, open the dashboard.
4. **Failure handling (2 min):** show quality rollback and out-of-order tests. Explain local transaction scope versus per-table Delta transactions.
5. **Privacy (1 min):** explain HMAC tokens, raw bronze restrictions, key rotation, and why pseudonymization is not anonymization.
6. **Deployment (1 min):** walk through CI, manual dev CD, bundle variables, and Terraform prerequisites.
7. **Tradeoffs and next steps (2 min):** discuss decimals, source sequence numbers, freshness SLOs, access audits, integration tests, and incremental ingestion.

## Mapping to roles

| Senior responsibility | Evidence to discuss |
|---|---|
| Python / SQL engineering | Contract module, transactional pipeline, reporting views |
| Spark / Databricks / Delta | MERGE adapter and bundle job |
| Analytics engineering | dbt staging/fact models and reconciliation |
| DevOps / IaC | GitHub Actions, Docker, Terraform baseline |
| End-to-end ownership | Operations runbook, audit rows, recovery design |
| Governance | Product catalog, tokenization, example least-privilege grants |
| AI enablement | Reusable feature preparation without a decision model |
| Stakeholder communication | Business grain definitions and documented limitations |

Use honest language in an application: “Built a synthetic lending data platform with a tested local pipeline and a Databricks deployment adapter.” Describe cloud deployment experience only after running and validating it in your own tenant.
