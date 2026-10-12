# Cloud deployment

## Databricks development job

The bundle follows the [official Python wheel bundle pattern](https://docs.databricks.com/gcp/en/dev-tools/bundles/python-wheel). Review the [Azure examples](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/examples) for your workspace runtime.

Prerequisites:
1. Databricks CLI and Python build package installed.
2. A compatible existing cluster with Spark 3.5+ and built-in Delta support. Select a runtime supported by your workspace.
3. A Unity Catalog catalog with permission to create a demo schema and tables.
4. A secret scope containing a random token key of at least 16 characters.
5. Synthetic JSONL uploaded to a Unity Catalog Volume readable by the job identity.
6. A Databricks authentication profile or environment credentials.

```bash
pip install build
databricks bundle validate -t dev \
  --var cluster_id=YOUR_CLUSTER,input_path=/Volumes/YOUR_CATALOG/YOUR_SCHEMA/YOUR_VOLUME/applications.jsonl,catalog=YOUR_CATALOG
databricks bundle deploy -t dev \
  --var cluster_id=YOUR_CLUSTER,input_path=/Volumes/YOUR_CATALOG/YOUR_SCHEMA/YOUR_VOLUME/applications.jsonl,catalog=YOUR_CATALOG
databricks bundle run creditflow -t dev \
  --var cluster_id=YOUR_CLUSTER,input_path=/Volumes/YOUR_CATALOG/YOUR_SCHEMA/YOUR_VOLUME/applications.jsonl,catalog=YOUR_CATALOG
```

Use a secret manager or workspace secret scope. Never put keys into notebook output, Terraform variables committed to Git, or workflow logs. Before analytics access, adapt and review `governance/access.sql` using real account group names.

The Spark adapter is syntax-checked locally but has not been executed in a Databricks workspace. The first cloud run should use a small synthetic batch, then a replay and an invalid batch. Confirm Delta versions, table grants, unchanged silver after a rejected batch, and convergence of out-of-order events.

## Manual CD workflow

The deployment workflow is started manually and targets the GitHub `databricks-dev` environment. Configure:
- Secrets: `DATABRICKS_HOST`, `DATABRICKS_TOKEN`.
- Environment variables: `DATABRICKS_CLUSTER_ID`, `CREDITFLOW_INPUT_PATH`, `CREDITFLOW_CATALOG`.
- Optional environment protection rules for deployment review.

This deploys job definitions only. It does not run the job or create cloud resources. Service principal/OIDC authentication is the preferred next step for a production tenant; the supplied workflow uses a scoped development token.

## Terraform baseline

`infra/main.tf` creates an Azure resource group, ADLS Gen2 storage account, premium Databricks workspace, and Azure Data Factory identity. This is a baseline, not a turnkey network topology.

Storage has public networking and shared access keys disabled. **Private endpoints, private DNS, VNet integration, managed identity/RBAC, and Unity Catalog external locations must be configured before the job can read that storage account.** The Databricks job can instead use an existing accessible Unity Catalog Volume.

The ADF resource is an infrastructure example; no ADF copy pipeline or linked service is implemented. Airflow/Databricks supply orchestration in this repository.

```bash
cd infra
terraform init
terraform validate
terraform plan -var-file=.example.tfvars
```

Replace the example subscription ID and globally unique storage prefix locally. Provision only after reviewing estimated subscription costs and network design. No cloud resources have been created for this project. State must use an approved encrypted remote backend before shared use.
