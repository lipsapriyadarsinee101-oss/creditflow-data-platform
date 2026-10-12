"""Shared source contract and explicit rejection reasons."""
from datetime import date, datetime
import math

FIELDS = {"application_id", "customer_id", "updated_at", "application_date", "amount_eur", "income_eur", "term_months", "status", "channel"}
STATUSES = {"approved", "rejected", "pending"}
CHANNELS = {"broker", "direct", "partner"}


def validate(row: dict) -> list[str]:
    errors = []
    if not isinstance(row, dict):
        return ["row_not_object"]
    missing = FIELDS - row.keys()
    if missing:
        return ["missing_fields:" + ",".join(sorted(missing))]
    for field in ("application_id", "customer_id"):
        if not isinstance(row[field], str) or not row[field].strip():
            errors.append(field + "_invalid")
    for field in ("amount_eur", "income_eur"):
        value = row[field]
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value <= 0:
            errors.append(field + "_invalid")
    if type(row["term_months"]) is not int or row["term_months"] not in (12, 24, 36, 48, 60, 72):
        errors.append("term_months_invalid")
    if not isinstance(row["status"], str) or row["status"] not in STATUSES:
        errors.append("status_invalid")
    if not isinstance(row["channel"], str) or row["channel"] not in CHANNELS:
        errors.append("channel_invalid")
    try:
        date.fromisoformat(row["application_date"])
        timestamp = datetime.fromisoformat(row["updated_at"])
        if timestamp.tzinfo is None:
            errors.append("updated_at_timezone_missing")
    except (ValueError, TypeError):
        errors.append("date_invalid")
    return errors
