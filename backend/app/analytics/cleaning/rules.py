import math
from datetime import UTC, date, datetime
from typing import Any

from app.schemas.data_quality import QualityDimensionsScore

MISSING_SENTINELS = {
    "",
    " ",
    "na",
    "n/a",
    "nan",
    "null",
    "none",
    "?",
    "-",
    "--",
    "nil",
    "undefined",
    "empty",
}

CUSTOMER_TYPE_MAP = {
    "b2b": "B2B",
    "b-to-b": "B2B",
    "business": "B2B",
    "b2c": "B2C",
    "b-to-c": "B2C",
    "consumer": "B2C",
    "retail": "B2C",
    "enterprise": "Enterprise",
    "corp": "Enterprise",
    "corporate": "Enterprise",
}

SALES_CHANNEL_MAP = {
    "direct": "Direct",
    "online": "Online",
    "retail": "Retail",
    "partner": "Partner",
    "wholesale": "Wholesale",
}

ORDER_STATUS_MAP = {
    "completed": "Completed",
    "pending": "Pending",
    "cancelled": "Cancelled",
    "canceled": "Cancelled",
    "refunded": "Refunded",
    "shipped": "Shipped",
    "delivered": "Delivered",
}

ACQUISITION_CHANNEL_MAP = {
    "organic search": "Organic Search",
    "organic": "Organic Search",
    "paid search": "Paid Search",
    "paid": "Paid Search",
    "email": "Email",
    "referral": "Referral",
    "social media": "Social Media",
    "social": "Social Media",
    "direct": "Direct",
}


def is_missing(val: Any) -> bool:
    """Return True if value represents a missing, blank, or sentinel null value."""
    if val is None:
        return True
    if isinstance(val, float) and math.isnan(val):
        return True
    if isinstance(val, str):
        clean_str = val.strip().lower()
        return clean_str in MISSING_SENTINELS
    return False


def validate_numeric(
    val: Any,
    field_name: str,
    min_val: float = 0.0,
    max_val: float | None = None,
) -> tuple[bool, float | None, str | None]:
    """Validate numeric ranges and formatting."""
    if is_missing(val):
        return False, None, f"{field_name} is missing"
    try:
        clean_num_str = str(val).strip().replace("$", "").replace(",", "")
        num = float(clean_num_str)
        if math.isnan(num) or math.isinf(num):
            return False, None, f"{field_name} is NaN or Inf"
        if num < min_val:
            return False, num, f"{field_name} ({num}) is less than minimum allowed ({min_val})"
        if max_val is not None and num > max_val:
            return False, num, f"{field_name} ({num}) exceeds maximum allowed ({max_val})"
        return True, num, None
    except (ValueError, TypeError):
        return False, None, f"{field_name} '{val}' is not a valid number"


def validate_date(
    val: Any,
    field_name: str,
    allow_future: bool = False,
) -> tuple[bool, date | None, str | None]:
    """Validate date strings against supported formats and boundary conditions."""
    if is_missing(val):
        return False, None, f"{field_name} is missing"

    date_str = str(val).strip()
    parsed_date: date | None = None

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%m/%d/%Y", "%Y%m%d"):
        try:
            parsed_date = datetime.strptime(date_str, fmt).date()
            break
        except ValueError:
            continue

    if parsed_date is None:
        return False, None, f"{field_name} '{val}' is not a valid recognized date"

    today_utc = datetime.now(UTC).date()
    if not allow_future and parsed_date > today_utc:
        return (
            False,
            parsed_date,
            f"{field_name} ({parsed_date}) is in the future beyond today ({today_utc})",
        )

    # Historical sanity check (e.g. no dates earlier than 2000 for modern business records)
    if parsed_date.year < 2000:
        return (
            False,
            parsed_date,
            f"{field_name} ({parsed_date}) is unreasonably old (prior to year 2000)",
        )

    return True, parsed_date, None


def standardize_category(
    val: Any,
    category_map: dict[str, str],
    default: str | None = None,
) -> tuple[str | None, bool]:
    """Standardize category values using normalized lookup maps."""
    if is_missing(val):
        return default, False

    clean_str = str(val).strip().lower()
    if clean_str in category_map:
        standardized = category_map[clean_str]
        changed = str(val) != standardized
        return standardized, changed

    title_cased = str(val).strip().title()
    return title_cased, title_cased != str(val)


def validate_referential_integrity(
    val: Any,
    valid_ids: set[Any],
    field_name: str,
) -> tuple[bool, str | None]:
    """Verify that foreign key values exist in parent database tables."""
    if is_missing(val):
        return False, f"{field_name} foreign key is missing"

    try:
        if isinstance(val, str) and val.isdigit():
            val = int(val)
        if val in valid_ids:
            return True, None
        return False, f"Foreign key violation: {field_name}={val} does not exist in target table"
    except Exception as e:
        return False, f"Invalid foreign key check on {field_name}: {e}"


def detect_duplicates(
    records: list[dict[str, Any]],
    key_fields: list[str],
) -> tuple[set[int], list[dict[str, Any]]]:
    """
    Detect duplicate records based on business key fields or complete row equality.
    Returns:
        tuple of (duplicate_row_indices_set_starting_at_1, details_list)
    """
    seen_keys: set[tuple[Any, ...]] = set()
    duplicate_rows: set[int] = set()
    duplicate_details: list[dict[str, Any]] = []

    for idx, row in enumerate(records, start=1):
        key: tuple[Any, ...]
        if key_fields:
            key = tuple(str(row.get(k, "")).strip().lower() for k in key_fields)
        else:
            key = tuple(sorted((k, str(v).strip()) for k, v in row.items()))

        if key in seen_keys:
            duplicate_rows.add(idx)
            duplicate_details.append(
                {
                    "row_number": idx,
                    "key_fields": key_fields,
                    "duplicate_key": str(key),
                }
            )
        else:
            seen_keys.add(key)

    return duplicate_rows, duplicate_details


def calculate_quality_dimensions(
    total_records: int,
    missing_required_cells: int,
    total_required_cells: int,
    invalid_field_checks: int,
    total_field_checks: int,
    duplicate_records: int,
    inconsistent_cells: int,
    total_consistency_checks: int,
    timely_records: int,
) -> QualityDimensionsScore:
    """
    Compute the 5 official Nexora data quality dimensions and the overall composite score.
    Formulas:
        Completeness = (1 - missing_required / total_required) * 100
        Validity     = (1 - invalid_checks / total_checks) * 100
        Uniqueness   = (1 - duplicate_records / total_records) * 100
        Consistency  = (1 - inconsistent_cells / total_consistency_checks) * 100
        Timeliness   = (timely_records / total_records) * 100
        Overall Score = (
            0.25*Completeness + 0.25*Validity + 0.20*Uniqueness
            + 0.20*Consistency + 0.10*Timeliness
        )
    """
    if total_records == 0:
        return QualityDimensionsScore(
            completeness=100.0,
            uniqueness=100.0,
            validity=100.0,
            consistency=100.0,
            timeliness=100.0,
            overall_score=100.0,
        )

    # Completeness
    completeness = (
        (1.0 - (missing_required_cells / total_required_cells)) * 100.0
        if total_required_cells > 0
        else 100.0
    )

    # Validity
    validity = (
        (1.0 - (invalid_field_checks / total_field_checks)) * 100.0
        if total_field_checks > 0
        else 100.0
    )

    # Uniqueness
    uniqueness = (1.0 - (duplicate_records / total_records)) * 100.0 if total_records > 0 else 100.0

    # Consistency
    consistency = (
        (1.0 - (inconsistent_cells / total_consistency_checks)) * 100.0
        if total_consistency_checks > 0
        else 100.0
    )

    # Timeliness
    timeliness = (timely_records / total_records) * 100.0 if total_records > 0 else 100.0

    # Clamp each between 0.0 and 100.0
    completeness = max(0.0, min(100.0, round(completeness, 2)))
    validity = max(0.0, min(100.0, round(validity, 2)))
    uniqueness = max(0.0, min(100.0, round(uniqueness, 2)))
    consistency = max(0.0, min(100.0, round(consistency, 2)))
    timeliness = max(0.0, min(100.0, round(timeliness, 2)))

    # Overall weighted composite
    overall = (
        0.25 * completeness
        + 0.25 * validity
        + 0.20 * uniqueness
        + 0.20 * consistency
        + 0.10 * timeliness
    )
    overall = max(0.0, min(100.0, round(overall, 2)))

    return QualityDimensionsScore(
        completeness=completeness,
        uniqueness=uniqueness,
        validity=validity,
        consistency=consistency,
        timeliness=timeliness,
        overall_score=overall,
    )
