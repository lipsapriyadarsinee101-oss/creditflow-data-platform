# Privacy, access, and boundaries

All generated records are synthetic. The project is designed to illustrate privacy-aware engineering, not to certify GDPR compliance.

| Layer | Information | Intended access |
|---|---|---|
| Source / bronze | Raw synthetic customer ID and payload | Ingestion engineers |
| Quarantine | Event hash and validation reasons; raw details remain in bronze | Data operations |
| Silver | Pseudonymous customer token and application-level facts | Restricted engineering |
| Gold daily | Daily channel-level counts and volumes | Analytics consumers |
| Gold features | Application ID and derived ratios | Restricted data science |

Customer identifiers never appear in the aggregate API. Small-group aggregates can still disclose information when real records replace synthetic ones; suppression rules and minimum group sizes must be designed with data owners.

The HTTP service binds localhost by default and provides no authentication, TLS, or rate limiting. Do not expose it publicly with real data. A production API needs an authenticated gateway, authorization, audit trails, freshness policy, and query limits.

The included SQL grants are examples for an existing Unity Catalog deployment. They do not create groups, provision identities, revoke inherited access, or grant tenant-wide compliance. Review effective permissions at catalog, schema, table/view, volume, and workspace levels.

No repository file should contain credentials, customer exports, private job listings, or Terraform state. Generated data and local state are excluded by `.gitignore`. The original pasted job descriptions are not included in the repository.
