# Contributing

Run the Python integration suite and dbt build before opening a pull request. Keep synthetic sample data deterministic and do not commit credentials or real customer records.

For contract changes, update the shared validation module, tests, Spark assumptions, product metadata, and consumer documentation together. State migration/rebuild requirements explicitly.

For infrastructure changes, attach a Terraform plan generated against a sandbox subscription with sensitive values redacted. A passing local pipeline test does not substitute for a Databricks integration run.
