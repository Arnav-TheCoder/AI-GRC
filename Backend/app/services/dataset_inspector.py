import csv
from collections import Counter
from pathlib import Path

MAX_ROWS = 100000
MAX_COLUMNS = 250


def inspect_csv(path: str) -> dict:
    """Read CSV as data only. Never evaluate formulas or execute content."""
    result = {"analysis_status": "completed", "format": "CSV", "row_count": 0,
              "column_count": 0, "columns": [], "warnings": [], "sampled": False}
    try:
        with open(path, "r", encoding="utf-8-sig", newline="", errors="replace") as handle:
            reader = csv.DictReader(handle)
            headers = reader.fieldnames or []
            if not headers:
                return {**result, "analysis_status": "failed", "warnings": ["CSV header row is missing or empty."]}
            if len(headers) > MAX_COLUMNS:
                headers = headers[:MAX_COLUMNS]
                result["warnings"].append(f"Only the first {MAX_COLUMNS} columns were analysed.")
            stats = {h: {"missing": 0, "types": Counter(), "unique": set(), "numeric_min": None, "numeric_max": None} for h in headers}
            rows = 0
            for row in reader:
                rows += 1
                for h in headers:
                    value = (row.get(h) or "").strip()
                    s = stats[h]
                    if not value:
                        s["missing"] += 1
                        continue
                    if len(s["unique"]) < 1000:
                        s["unique"].add(value[:256])
                    try:
                        number = float(value)
                        s["types"]["numeric"] += 1
                        s["numeric_min"] = number if s["numeric_min"] is None else min(s["numeric_min"], number)
                        s["numeric_max"] = number if s["numeric_max"] is None else max(s["numeric_max"], number)
                    except ValueError:
                        low = value.lower()
                        if low in {"true", "false", "yes", "no"}:
                            s["types"]["boolean-like"] += 1
                        else:
                            s["types"]["text"] += 1
                if rows >= MAX_ROWS:
                    result["sampled"] = True
                    break
            result["row_count"] = rows
            result["column_count"] = len(headers)
            result["columns"] = []
            for h in headers:
                s = stats[h]
                dominant = s["types"].most_common(1)[0][0] if s["types"] else "empty"
                item = {"name": h, "inferred_type": dominant, "missing_count": s["missing"],
                        "missing_percent": round((s["missing"] / max(rows, 1)) * 100, 2),
                        "unique_values_sample": len(s["unique"])}
                if dominant == "numeric":
                    item["numeric_min"] = s["numeric_min"]
                    item["numeric_max"] = s["numeric_max"]
                result["columns"].append(item)
            if rows == 0:
                result["warnings"].append("CSV contains headers but no data rows.")
            if result["sampled"]:
                result["warnings"].append(f"Analysis stopped after {MAX_ROWS} rows; row count is a minimum.")
            if any(c["missing_count"] for c in result["columns"]):
                result["warnings"].append("Missing values were detected in one or more columns.")
            return result
    except (OSError, csv.Error) as exc:
        return {**result, "analysis_status": "failed", "warnings": [f"CSV could not be analysed: {str(exc)[:200]}"]}
