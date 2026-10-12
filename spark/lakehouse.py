"""Databricks batch Delta pipeline. Requires the installed creditflow wheel."""
import argparse
import hashlib
import hmac
import json
import re
from datetime import datetime, timezone
from pyspark.sql import SparkSession, functions as F, types as T, Window
from delta.tables import DeltaTable
from creditflow.contracts import validate

SCHEMA = T.StructType([
    T.StructField("application_id", T.StringType()),
    T.StructField("customer_token", T.StringType()),
    T.StructField("updated_at", T.StringType()),
    T.StructField("application_date", T.StringType()),
    T.StructField("amount_eur", T.DoubleType()),
    T.StructField("income_eur", T.DoubleType()),
    T.StructField("term_months", T.IntegerType()),
    T.StructField("status", T.StringType()),
    T.StructField("channel", T.StringType()),
    T.StructField("error", T.StringType()),
])

def process(spark, source, catalog, schema, secret, max_reject_ratio=0.05):
    for name in (catalog, schema):
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError("Catalog/schema must be simple SQL identifiers")
    if len(secret) < 16 or not 0 <= max_reject_ratio <= 1:
        raise ValueError("Invalid key or quality threshold")
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    prefix = f"{catalog}.{schema}"
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {prefix}")
    spark.sql(f"CREATE TABLE IF NOT EXISTS {prefix}.metadata (key STRING, value STRING) USING DELTA")
    fingerprint = hashlib.sha256(secret.encode()).hexdigest()
    old = spark.table(f"{prefix}.metadata").where("key = 'key_fingerprint'").collect()
    if old and old[0].value != fingerprint:
        raise ValueError("Key rotation requires full rebuild")
    if not old:
        spark.createDataFrame([("key_fingerprint", fingerprint)], ["key", "value"]).write.mode("append").saveAsTable(f"{prefix}.metadata")

    def parse(payload):
        try:
            row = json.loads(payload)
            errors = validate(row)
            if errors:
                return (None,) * 9 + (",".join(errors),)
            token = hmac.new(secret.encode(), row["customer_id"].encode(), hashlib.sha256).hexdigest()
            stamp = datetime.fromisoformat(row["updated_at"]).astimezone(timezone.utc).isoformat()
            return (row["application_id"], token, stamp, row["application_date"],
                    float(row["amount_eur"]), float(row["income_eur"]), row["term_months"],
                    row["status"], row["channel"], None)
        except (ValueError, TypeError):
            return (None,) * 9 + ("invalid_json",)

    raw = spark.read.text(source).where(F.length(F.trim("value")) > 0)
    raw = raw.select(F.trim("value").alias("payload")).withColumn("event_hash", F.sha2("payload", 256)).dropDuplicates(["event_hash"])
    def merge_insert(frame, table, key):
        if not spark.catalog.tableExists(table):
            frame.write.format("delta").mode("error").saveAsTable(table)
        else:
            DeltaTable.forName(spark, table).alias("t").merge(frame.alias("s"), f"t.{key}=s.{key}").whenNotMatchedInsertAll().execute()
    merge_insert(raw, f"{prefix}.bronze", "event_hash")
    parsed = raw.withColumn("record", F.udf(parse, SCHEMA)("payload")).select("event_hash", "record.*").cache()
    try:
        total = parsed.count()
        if not total:
            raise ValueError("Empty input")
        rejected = parsed.where("error IS NOT NULL")
        bad = rejected.count()
        merge_insert(rejected.select("event_hash", "error"), f"{prefix}.quarantine", "event_hash")
        if bad / total > max_reject_ratio:
            raise ValueError("Quality gate failed; bronze/quarantine retained, silver unchanged")
        order = Window.partitionBy("application_id").orderBy(F.desc("updated_at"), F.desc("event_hash"))
        silver = parsed.where("error IS NULL").drop("error").withColumn("rank", F.row_number().over(order)).where("rank=1").drop("rank")
        table = f"{prefix}.silver"
        if not spark.catalog.tableExists(table):
            silver.write.format("delta").saveAsTable(table)
        else:
            (DeltaTable.forName(spark, table).alias("t").merge(silver.alias("s"), "t.application_id=s.application_id")
             .whenMatchedUpdateAll(condition="s.updated_at > t.updated_at OR (s.updated_at=t.updated_at AND s.event_hash>t.event_hash)")
             .whenNotMatchedInsertAll().execute())
        spark.sql(f"""CREATE OR REPLACE VIEW {prefix}.gold_daily AS
            SELECT application_date, channel, COUNT(*) applications,
            SUM(CASE WHEN status='approved' THEN 1 ELSE 0 END) approved,
            SUM(CASE WHEN status='approved' THEN amount_eur ELSE 0 END) approved_volume_eur,
            AVG(amount_eur) average_requested_eur
            FROM {table} GROUP BY application_date, channel""")
        spark.sql(f"""CREATE OR REPLACE VIEW {prefix}.gold_features AS
            SELECT application_id, amount_eur/income_eur loan_to_monthly_income,
            amount_eur/term_months/income_eur principal_payment_to_income,
            term_months, channel FROM {table}""")
        print(json.dumps({"input_events": total, "rejected": bad, "silver_candidates": silver.count()}))
    finally:
        parsed.unpersist()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("input", "catalog", "schema", "secret-scope", "secret-key"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    spark = SparkSession.builder.getOrCreate()
    from pyspark.dbutils import DBUtils
    secret = DBUtils(spark).secrets.get(args.secret_scope, args.secret_key)
    process(spark, args.input, args.catalog, args.schema, secret)
