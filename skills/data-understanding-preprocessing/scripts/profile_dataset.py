#!/usr/bin/env python3
"""Profile a CSV dataset for pre-modeling data understanding."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


MISSING_TOKENS = {"", "na", "n/a", "null", "none", "nan", ".", "missing"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Profile a CSV file for data understanding and preprocessing."
    )
    parser.add_argument("csv_path", help="Path to the CSV file to profile.")
    parser.add_argument("--delimiter", default=None, help="CSV delimiter. Defaults to sniffing.")
    parser.add_argument("--encoding", default="utf-8", help="File encoding. Default: utf-8.")
    parser.add_argument("--target", default=None, help="Optional target column name.")
    parser.add_argument("--id-column", default=None, help="Optional subject/record ID column name.")
    parser.add_argument("--time-column", default=None, help="Optional prediction, event, or observation time column name.")
    parser.add_argument("--group-column", default=None, help="Optional subject/cluster/site column name for grouped or repeated-measures data.")
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=20000,
        help="Maximum rows to scan. Use 0 to scan all rows. Default: 20000.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Number of top categorical values to report. Default: 10.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of Markdown.",
    )
    return parser.parse_args()


def is_missing(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() in MISSING_TOKENS


def try_float(value: str) -> float | None:
    try:
        parsed = float(value.replace(",", ""))
    except ValueError:
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def try_datetime(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    candidates = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%b %d %Y",
        "%B %d %Y",
    ]
    if text.endswith("Z"):
        text = text[:-1]
    for fmt in candidates:
        try:
            datetime.strptime(text, fmt)
            return True
        except ValueError:
            pass
    try:
        datetime.fromisoformat(text)
        return True
    except ValueError:
        return False


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = (len(ordered) - 1) * q
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return ordered[int(idx)]
    return ordered[lo] * (hi - idx) + ordered[hi] * (idx - lo)


def infer_type(stats: dict[str, Any], rows_seen: int) -> str:
    non_missing = stats["non_missing"]
    if non_missing == 0:
        return "all_missing"
    unique_count = len(stats["values"])
    unique_ratio = unique_count / max(non_missing, 1)
    name = stats["name"].lower()
    numeric_ratio = stats["numeric_count"] / non_missing
    datetime_ratio = stats["datetime_count"] / non_missing
    bool_values = {v.strip().lower() for v in stats["values"]}

    if unique_count == 1:
        return "constant"
    # Check parseable-datetime before the high-uniqueness ID heuristic, so unique timestamps
    # (common in EHR data, and leakage-relevant) are not misclassified as IDs.
    if datetime_ratio >= 0.8:
        return "datetime"
    if name.endswith("_id") or name == "id" or "uuid" in name or unique_ratio > 0.95:
        return "id_like"
    if bool_values <= {"0", "1", "true", "false", "yes", "no", "y", "n"} and unique_count <= 2:
        return "binary"
    if numeric_ratio >= 0.95:
        numeric_values = stats["numeric_values"]
        integer_like = all(float(v).is_integer() for v in numeric_values)
        if integer_like and unique_count <= min(20, max(2, rows_seen // 20)):
            return "numeric_discrete_or_ordinal_candidate"
        if integer_like:
            return "count_or_integer_numeric"
        return "numeric_continuous"
    if stats["max_length"] >= 80 or stats["avg_length"] >= 40:
        return "text"
    if unique_count <= max(20, int(non_missing * 0.05)):
        return "categorical"
    return "string_or_high_cardinality_categorical"


def infer_role_hints(name: str, inferred_type: str, explicit_roles: dict[str, str | None]) -> list[str]:
    lower = name.lower()
    hints = []
    for role, column in explicit_roles.items():
        if column and name == column:
            hints.append(role)
    if lower in {"target", "label", "outcome", "y"} or any(token in lower for token in ["target", "label", "outcome"]):
        hints.append("target_candidate")
    if lower == "id" or lower.endswith("_id") or "uuid" in lower or inferred_type == "id_like":
        hints.append("id_candidate")
    if any(token in lower for token in ["date", "time", "timestamp", "dt"]) or inferred_type == "datetime":
        hints.append("time_candidate")
    if any(token in lower for token in ["group", "entity", "user", "customer", "patient", "account", "site", "store"]):
        hints.append("group_candidate")
    if any(token in lower for token in ["weight", "sample_weight"]):
        hints.append("weight_candidate")
    if any(token in lower for token in ["offset", "exposure", "denominator"]):
        hints.append("offset_or_exposure_candidate")
    return sorted(set(hints))


def leakage_name_hints(name: str) -> list[str]:
    lower = name.lower()
    patterns = {
        "target_or_label_name": ["target", "label", "outcome", "response"],
        "future_or_post_event_name": ["future", "after", "post", "next", "later"],
        "result_or_status_name": ["result", "status", "disposition", "resolved", "closed"],
        "score_or_probability_name": ["score", "prob", "risk", "prediction"],
        "manual_review_name": ["review", "adjudication", "verified", "approved"],
    }
    return [reason for reason, tokens in patterns.items() if any(token in lower for token in tokens)]


def suggest_task_type(inferred_type: str, unique_count: int, non_missing: int) -> str:
    if inferred_type == "binary":
        return "binary_classification_candidate"
    if inferred_type in {"categorical", "numeric_discrete_or_ordinal_candidate"} and unique_count <= 20:
        return "multiclass_or_ordinal_classification_candidate"
    if inferred_type in {"numeric_continuous", "count_or_integer_numeric"}:
        if unique_count <= max(20, int(non_missing * 0.05)):
            return "count_or_ordinal_prediction_candidate"
        return "regression_candidate"
    if inferred_type == "datetime":
        return "time_to_event_or_forecasting_target_candidate"
    return "requires_task_confirmation"


def duplicate_key_summary(
    path: Path,
    dialect: csv.Dialect,
    encoding: str,
    key_columns: list[str],
    sample_rows: int,
) -> dict[str, Any] | None:
    if not key_columns:
        return None
    counter: Counter[tuple[str, ...]] = Counter()
    rows_seen = 0
    missing_key_rows = 0
    with path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle, dialect=dialect)
        fieldnames = set(reader.fieldnames or [])
        missing_columns = [column for column in key_columns if column not in fieldnames]
        if missing_columns:
            return {"key_columns": key_columns, "missing_key_columns": missing_columns}
        for row in reader:
            if sample_rows and rows_seen >= sample_rows:
                break
            rows_seen += 1
            key = tuple((row.get(column, "") or "").strip() for column in key_columns)
            if any(is_missing(value) for value in key):
                missing_key_rows += 1
            counter[key] += 1
    duplicate_keys = sum(count - 1 for count in counter.values() if count > 1)
    return {
        "key_columns": key_columns,
        "rows_checked": rows_seen,
        "missing_key_rows": missing_key_rows,
        "duplicate_key_rows": duplicate_keys,
        "unique_keys": len(counter),
    }


def sniff_dialect(path: Path, encoding: str, delimiter: str | None) -> csv.Dialect:
    with path.open("r", encoding=encoding, newline="") as handle:
        sample = handle.read(8192)
    if delimiter:
        class CustomDialect(csv.excel):
            pass

        CustomDialect.delimiter = delimiter
        return CustomDialect
    try:
        return csv.Sniffer().sniff(sample)
    except csv.Error:
        return csv.excel


def profile_csv(
    path: Path,
    delimiter: str | None,
    encoding: str,
    sample_rows: int,
    top_n: int,
    target: str | None = None,
    id_column: str | None = None,
    time_column: str | None = None,
    group_column: str | None = None,
) -> dict[str, Any]:
    dialect = sniff_dialect(path, encoding, delimiter)
    columns: dict[str, dict[str, Any]] = {}
    duplicate_counter: Counter[tuple[str, ...]] = Counter()
    rows_seen = 0
    rows_with_missing = 0

    with path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle, dialect=dialect)
        if reader.fieldnames is None:
            raise ValueError("CSV file has no header row.")
        fieldnames = [field or "" for field in reader.fieldnames]
        duplicate_headers = [name for name, count in Counter(fieldnames).items() if count > 1]
        for name in fieldnames:
            columns[name] = {
                "name": name,
                "missing": 0,
                "non_missing": 0,
                "values": Counter(),
                "numeric_count": 0,
                "datetime_count": 0,
                "numeric_values": [],
                "min_length": None,
                "max_length": 0,
                "total_length": 0,
                "examples": [],
            }

        for row in reader:
            if sample_rows and rows_seen >= sample_rows:
                break
            rows_seen += 1
            row_values = tuple(row.get(name, "") or "" for name in fieldnames)
            duplicate_counter[row_values] += 1
            row_missing = False

            for name in fieldnames:
                raw = row.get(name, "")
                value = "" if raw is None else raw.strip()
                stats = columns[name]
                if is_missing(value):
                    stats["missing"] += 1
                    row_missing = True
                    continue

                stats["non_missing"] += 1
                stats["values"][value] += 1
                length = len(value)
                stats["min_length"] = length if stats["min_length"] is None else min(stats["min_length"], length)
                stats["max_length"] = max(stats["max_length"], length)
                stats["total_length"] += length
                if len(stats["examples"]) < 5 and value not in stats["examples"]:
                    stats["examples"].append(value)

                number = try_float(value)
                if number is not None:
                    stats["numeric_count"] += 1
                    if len(stats["numeric_values"]) < 50000:
                        stats["numeric_values"].append(number)
                if try_datetime(value):
                    stats["datetime_count"] += 1

            if row_missing:
                rows_with_missing += 1

    explicit_roles = {
        "target": target,
        "id": id_column,
        "time": time_column,
        "group": group_column,
    }
    column_reports = []
    target_report = None
    for name, stats in columns.items():
        non_missing = stats["non_missing"]
        numeric_values = stats["numeric_values"]
        inferred_type = infer_type(stats, rows_seen)
        report = {
            "name": name,
            "inferred_type": inferred_type,
            "role_hints": infer_role_hints(name, inferred_type, explicit_roles),
            "leakage_name_hints": leakage_name_hints(name),
            "missing_count": stats["missing"],
            "missing_pct": round(stats["missing"] / rows_seen * 100, 2) if rows_seen else None,
            "unique_count": len(stats["values"]),
            "unique_pct_non_missing": round(len(stats["values"]) / non_missing * 100, 2) if non_missing else None,
            "examples": stats["examples"],
            "top_values": stats["values"].most_common(top_n),
        }
        if non_missing:
            report["avg_length"] = round(stats["total_length"] / non_missing, 2)
            report["min_length"] = stats["min_length"]
            report["max_length"] = stats["max_length"]
        if numeric_values:
            q1 = percentile(numeric_values, 0.25)
            q3 = percentile(numeric_values, 0.75)
            iqr = None if q1 is None or q3 is None else q3 - q1
            report["numeric_summary"] = {
                "min": min(numeric_values),
                "q1": q1,
                "median": percentile(numeric_values, 0.5),
                "mean": statistics.fmean(numeric_values),
                "q3": q3,
                "max": max(numeric_values),
                "iqr": iqr,
                "possible_low_outlier_cutoff": None if iqr is None else q1 - 1.5 * iqr,
                "possible_high_outlier_cutoff": None if iqr is None else q3 + 1.5 * iqr,
            }
        column_reports.append(report)
        if target and name == target:
            target_report = {
                "name": name,
                "inferred_type": inferred_type,
                "missing_count": report["missing_count"],
                "missing_pct": report["missing_pct"],
                "unique_count": report["unique_count"],
                "top_values": report["top_values"],
                "numeric_summary": report.get("numeric_summary"),
                "suggested_task_type": suggest_task_type(inferred_type, report["unique_count"], non_missing),
            }

    duplicate_rows = sum(count - 1 for count in duplicate_counter.values() if count > 1)
    key_checks = {}
    if id_column:
        key_checks["id_column"] = duplicate_key_summary(path, dialect, encoding, [id_column], sample_rows)
    if group_column and time_column:
        key_checks["group_time"] = duplicate_key_summary(path, dialect, encoding, [group_column, time_column], sample_rows)
    return {
        "path": str(path),
        "rows_profiled": rows_seen,
        "columns": len(columns),
        "duplicate_header_names": duplicate_headers,
        "duplicate_rows_in_profile": duplicate_rows,
        "rows_with_missing": rows_with_missing,
        "rows_with_missing_pct": round(rows_with_missing / rows_seen * 100, 2) if rows_seen else None,
        "explicit_roles": explicit_roles,
        "target_report": target_report,
        "key_checks": key_checks,
        "column_profiles": column_reports,
    }


def render_markdown(profile: dict[str, Any]) -> str:
    lines = [
        "# Dataset Profile",
        "",
        f"- Path: `{profile['path']}`",
        f"- Rows profiled: {profile['rows_profiled']}",
        f"- Columns: {profile['columns']}",
        f"- Duplicate header names: {profile['duplicate_header_names'] or 'none'}",
        f"- Duplicate rows in profiled sample: {profile['duplicate_rows_in_profile']}",
        f"- Rows with missing values: {profile['rows_with_missing']} ({profile['rows_with_missing_pct']}%)",
        f"- Explicit roles: {profile['explicit_roles']}",
        "",
    ]
    if profile["target_report"]:
        lines.extend(["## Target", "", f"- Summary: {profile['target_report']}", ""])
    if profile["key_checks"]:
        lines.extend(["## Key Checks", "", f"{profile['key_checks']}", ""])
    lines.extend(["## Columns", ""])
    for col in profile["column_profiles"]:
        lines.extend(
            [
                f"### {col['name']}",
                "",
                f"- Inferred type: {col['inferred_type']}",
                f"- Role hints: {col['role_hints']}",
                f"- Leakage name hints: {col['leakage_name_hints']}",
                f"- Missing: {col['missing_count']} ({col['missing_pct']}%)",
                f"- Unique non-missing values: {col['unique_count']} ({col['unique_pct_non_missing']}%)",
                f"- Examples: {col['examples']}",
            ]
        )
        if "numeric_summary" in col:
            summary = col["numeric_summary"]
            lines.append(
                "- Numeric summary: "
                f"min={summary['min']}, q1={summary['q1']}, median={summary['median']}, "
                f"mean={summary['mean']}, q3={summary['q3']}, max={summary['max']}"
            )
            lines.append(
                "- IQR outlier cutoffs: "
                f"low={summary['possible_low_outlier_cutoff']}, "
                f"high={summary['possible_high_outlier_cutoff']}"
            )
        lines.append(f"- Top values: {col['top_values']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    path = Path(args.csv_path).expanduser()
    if not path.exists():
        raise SystemExit(f"File not found: {path}")
    profile = profile_csv(
        path,
        args.delimiter,
        args.encoding,
        args.sample_rows,
        args.top_n,
        target=args.target,
        id_column=args.id_column,
        time_column=args.time_column,
        group_column=args.group_column,
    )
    if args.json:
        print(json.dumps(profile, indent=2, ensure_ascii=True))
    else:
        print(render_markdown(profile))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
