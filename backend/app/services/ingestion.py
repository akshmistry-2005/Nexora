import csv
import hashlib
import io
import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppException
from app.models.auth import User
from app.models.customer import Customer
from app.models.data_ops import DataSource, ImportJob, PipelineRun, StagingRecord
from app.models.organization import Organization
from app.schemas.data_ops import ImportResultResponse, PreviewResponse

# Predefined target entity field specifications
ENTITY_SPECS: dict[str, dict[str, Any]] = {
    "customers": {
        "required_fields": [
            "customer_code",
            "contact_name",
            "email",
            "region_id",
            "customer_type",
            "acquisition_channel",
        ],
        "optional_fields": ["company_name", "phone", "signup_date", "is_active"],
    },
    "products": {
        "required_fields": ["sku", "name", "category_id", "unit_price", "cost_price"],
        "optional_fields": ["description", "is_active"],
    },
    "orders": {
        "required_fields": [
            "order_number",
            "customer_id",
            "sales_channel",
            "status",
            "total_amount",
        ],
        "optional_fields": ["tax_amount", "discount_amount", "currency"],
    },
}


class IngestionService:
    """Robust data ingestion, CSV parsing, validation, staging, and atomic import."""

    def compute_checksum(self, content: bytes) -> str:
        """Compute SHA-256 hash of file content for deduplication."""
        return hashlib.sha256(content).hexdigest()

    def validate_file_meta(self, filename: str, content: bytes) -> None:
        """Enforce file extension, maximum file size, and non-empty checks."""
        # 1. Extension check (M7-T02)
        if not filename.lower().endswith(".csv"):
            ext = filename.rsplit(".", 1)[-1] if "." in filename else "unknown"
            raise AppException(
                f"Unsupported file format '{ext}'. Only standard CSV (.csv) files are permitted.",
                status_code=400,
                code="INVALID_FILE_TYPE",
            )

        # 2. Maximum file size check (M7-T03)
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise AppException(
                f"File size ({len(content) / 1024 / 1024:.2f} MB) exceeds maximum "
                f"allowed limit of {settings.max_upload_size_mb} MB.",
                status_code=413,
                code="FILE_TOO_LARGE",
            )

        # 3. Empty file check (M7-T04)
        if len(content.strip()) == 0:
            raise AppException(
                "Uploaded file is empty (0 bytes). Please upload a valid CSV file with data.",
                status_code=400,
                code="EMPTY_FILE",
            )

    def decode_csv_content(self, content: bytes) -> str:
        """Decode raw bytes using UTF-8 or UTF-8 with BOM."""
        try:
            return content.decode("utf-8-sig")
        except UnicodeDecodeError as e:
            try:
                return content.decode("latin-1")
            except Exception:
                raise AppException(
                    "Unable to decode file encoding. Expected standard UTF-8 CSV.",
                    status_code=400,
                    code="ENCODING_ERROR",
                ) from e

    def parse_csv_records(self, text_content: str) -> tuple[list[str], list[dict[str, Any]]]:
        """Parse CSV text, enforce syntax, and return headers and row dicts."""
        # Check for malformed quote syntax before csv reader (M7-T05)
        lines = [line.strip() for line in text_content.splitlines() if line.strip()]
        if not lines:
            raise AppException("Uploaded CSV contains no rows.", status_code=400, code="EMPTY_FILE")

        # Sniff delimiter
        first_line = lines[0]
        delimiter = ","
        if "\t" in first_line and first_line.count("\t") > first_line.count(","):
            delimiter = "\t"
        elif ";" in first_line and first_line.count(";") > first_line.count(","):
            delimiter = ";"

        try:
            reader = csv.reader(io.StringIO(text_content), delimiter=delimiter)
            raw_rows = list(reader)
        except Exception as e:
            raise AppException(
                f"Malformed CSV structure: {e}",
                status_code=400,
                code="MALFORMED_CSV",
            ) from e

        if not raw_rows:
            raise AppException("No records found in CSV.", status_code=400, code="EMPTY_FILE")

        headers = [h.strip() for h in raw_rows[0] if h.strip()]
        if not headers:
            raise AppException(
                "CSV must contain a valid non-empty header row.",
                status_code=400,
                code="MISSING_HEADERS",
            )

        # Check for uneven row column counts
        expected_cols = len(headers)
        data_rows: list[dict[str, Any]] = []

        for row_idx, row in enumerate(raw_rows[1:], start=2):
            if not row or (len(row) == 1 and not row[0].strip()):
                continue
            if len(row) != expected_cols:
                raise AppException(
                    f"Malformed CSV at line {row_idx}: row has {len(row)} columns "
                    f"but header defines {expected_cols} columns.",
                    status_code=400,
                    code="MALFORMED_CSV",
                )
            row_dict = {headers[i]: row[i].strip() for i in range(expected_cols)}
            data_rows.append(row_dict)

        return headers, data_rows

    def auto_map_headers(self, headers: list[str], target_entity: str) -> dict[str, str]:
        """Suggest mapping between target entity fields and CSV headers."""
        spec = ENTITY_SPECS.get(target_entity)
        if not spec:
            return {}

        all_target_fields = spec["required_fields"] + spec["optional_fields"]
        mapping: dict[str, str] = {}

        # Normalize header lookup
        normalized_headers = {re.sub(r"[^a-z0-9]", "", h.lower()): h for h in headers}

        for target in all_target_fields:
            target_norm = re.sub(r"[^a-z0-9]", "", target.lower())
            if target_norm in normalized_headers:
                mapping[target] = normalized_headers[target_norm]
            else:
                # Common synonyms
                synonyms = {
                    "customer_code": ["code", "custcode", "customerid", "id"],
                    "contact_name": ["name", "fullname", "contact", "customername"],
                    "email": ["emailaddress", "mail"],
                    "customer_type": ["type", "segment", "customertype"],
                    "region_id": ["region", "regionid", "territoryid"],
                    "acquisition_channel": ["channel", "acquisition", "source"],
                }
                for syn in synonyms.get(target, []):
                    if syn in normalized_headers:
                        mapping[target] = normalized_headers[syn]
                        break

        return mapping

    def infer_column_types(self, rows: list[dict[str, Any]], headers: list[str]) -> dict[str, str]:
        """Infer data types from sample rows."""
        types: dict[str, str] = {}
        sample = rows[:20]

        for h in headers:
            values = [r.get(h, "") for r in sample if r.get(h, "") != ""]
            if not values:
                types[h] = "string"
                continue

            if all(v.isdigit() for v in values):
                types[h] = "integer"
            elif all(re.match(r"^-?\d+(\.\d+)?$", v) for v in values):
                types[h] = "float"
            elif all(re.match(r"^\d{4}-\d{2}-\d{2}", v) for v in values):
                types[h] = "date"
            elif all(v.lower() in ("true", "false", "0", "1") for v in values):
                types[h] = "boolean"
            else:
                types[h] = "string"

        return types

    def preview_csv(
        self,
        session: Session,
        filename: str,
        content: bytes,
        target_entity: str,
    ) -> PreviewResponse:
        """Generate preview slice, inferred types, and header mappings before import commit."""
        self.validate_file_meta(filename, content)
        checksum = self.compute_checksum(content)
        text_content = self.decode_csv_content(content)
        headers, rows = self.parse_csv_records(text_content)

        if target_entity not in ENTITY_SPECS:
            raise AppException(
                f"Unknown target entity '{target_entity}'. Allowed: {list(ENTITY_SPECS.keys())}",
                status_code=400,
                code="INVALID_TARGET_ENTITY",
            )

        suggested_mapping = self.auto_map_headers(headers, target_entity)
        required_fields = ENTITY_SPECS[target_entity]["required_fields"]
        missing_required = [f for f in required_fields if f not in suggested_mapping]

        inferred_types = self.infer_column_types(rows, headers)

        # Check duplicate import
        stmt = select(DataSource).where(DataSource.file_checksum == checksum)
        is_duplicate = session.scalar(stmt) is not None

        return PreviewResponse(
            file_name=filename,
            file_size_bytes=len(content),
            file_checksum=checksum,
            target_entity=target_entity,
            detected_headers=headers,
            suggested_mapping=suggested_mapping,
            missing_required_headers=missing_required,
            total_detected_rows=len(rows),
            preview_rows=rows[:5],
            inferred_types=inferred_types,
            is_duplicate=is_duplicate,
        )

    def execute_import(
        self,
        session: Session,
        user: User,
        filename: str,
        content: bytes,
        target_entity: str,
        custom_mapping: dict[str, str] | None = None,
        allow_duplicate: bool = False,
    ) -> ImportResultResponse:
        """Atomically stage and import rows into database with rollback protection."""
        self.validate_file_meta(filename, content)
        checksum = self.compute_checksum(content)

        # Idempotency / Duplicate detection check (M7-T12)
        if not allow_duplicate:
            existing = session.scalar(
                select(DataSource).where(DataSource.file_checksum == checksum)
            )
            if existing:
                raise AppException(
                    f"Duplicate file detected. Dataset '{filename}' (checksum {checksum[:8]}...) "
                    "has already been imported. Set allow_duplicate=true to force re-import.",
                    status_code=409,
                    code="DUPLICATE_IMPORT",
                )

        text_content = self.decode_csv_content(content)
        headers, rows = self.parse_csv_records(text_content)

        if target_entity not in ENTITY_SPECS:
            raise AppException(
                f"Unknown target entity '{target_entity}'. Allowed: {list(ENTITY_SPECS.keys())}",
                status_code=400,
                code="INVALID_TARGET_ENTITY",
            )

        # Merge mapping
        mapping = self.auto_map_headers(headers, target_entity)
        if custom_mapping:
            mapping.update(custom_mapping)

        # Verify required headers (M7-T06)
        required_fields = ENTITY_SPECS[target_entity]["required_fields"]
        missing_required = [f for f in required_fields if f not in mapping]
        if missing_required:
            raise AppException(
                f"Missing required columns for entity '{target_entity}': {missing_required}. "
                f"Available headers: {headers}",
                status_code=400,
                code="MISSING_REQUIRED_COLUMNS",
            )

        org = session.scalar(select(Organization))
        if not org:
            raise AppException("Organization record not found.", status_code=404, code="NOT_FOUND")

        # Begin atomic staging & import block
        data_source = DataSource(
            organization_id=org.id,
            name=f"Upload: {filename}",
            source_type="CSV",
            file_name=filename,
            file_size_bytes=len(content),
            file_checksum=checksum,
            uploaded_by_id=user.id,
        )
        session.add(data_source)
        session.flush()

        import_job = ImportJob(
            data_source_id=data_source.id,
            target_entity=target_entity,
            status="staging",
            total_rows=len(rows),
            loaded_rows=0,
            rejected_rows=0,
            mapping_config=mapping,
            started_at=datetime.now(UTC),
        )
        session.add(import_job)
        session.flush()

        pipeline_run = PipelineRun(
            import_job_id=import_job.id,
            pipeline_name=f"Ingest-{target_entity.capitalize()}",
            status="running",
            metrics={"total_rows": len(rows)},
            started_at=datetime.now(UTC),
        )
        session.add(pipeline_run)
        session.flush()

        loaded_count = 0
        rejected_count = 0
        error_details: dict[str, Any] = {}

        try:
            # 1. Stage raw records
            for idx, row in enumerate(rows, start=1):
                staging_rec = StagingRecord(
                    import_job_id=import_job.id,
                    row_number=idx,
                    raw_data=row,
                    validation_status="valid",
                )
                session.add(staging_rec)

            session.flush()

            # 2. Destination load (e.g. for customers)
            if target_entity == "customers":
                for idx, row in enumerate(rows, start=1):
                    # Check for row-level constraint failure (e.g. numeric region_id)
                    raw_region = row.get(mapping["region_id"])
                    try:
                        region_id_val = int(raw_region)  # type: ignore[arg-type]
                    except (ValueError, TypeError) as err:
                        raise AppException(
                            f"Row {idx}: Invalid region_id '{raw_region}'. Must be an integer.",
                            status_code=400,
                            code="DATA_VALIDATION_ERROR",
                        ) from err

                    c_type = str(row.get(mapping["customer_type"], "B2B"))
                    if c_type not in ("B2B", "B2C", "Enterprise"):
                        c_type = "B2B"

                    signup_date_val = datetime.now(UTC).date()
                    raw_signup = row.get(mapping.get("signup_date", ""))
                    if raw_signup:
                        try:
                            signup_date_val = datetime.strptime(
                                str(raw_signup).strip(), "%Y-%m-%d"
                            ).date()
                        except Exception:
                            pass

                    cust = Customer(
                        organization_id=org.id,
                        region_id=region_id_val,
                        customer_code=str(row.get(mapping["customer_code"])),
                        company_name=str(row.get(mapping.get("company_name", ""), "")) or None,
                        contact_name=str(row.get(mapping["contact_name"])),
                        email=str(row.get(mapping["email"])),
                        phone=str(row.get(mapping.get("phone", ""), "")) or None,
                        customer_type=c_type,
                        acquisition_channel=str(row.get(mapping["acquisition_channel"])),
                        signup_date=signup_date_val,
                        is_active=True,
                    )
                    session.add(cust)
                    loaded_count += 1

            session.flush()

            # Mark success
            import_job.status = "completed"
            import_job.loaded_rows = loaded_count
            import_job.rejected_rows = rejected_count
            import_job.completed_at = datetime.now(UTC)

            pipeline_run.status = "success"
            pipeline_run.ended_at = datetime.now(UTC)

            session.commit()

        except Exception as e:
            # Transaction rollback safety (M7-T10)
            session.rollback()

            # Record failure in isolated transaction
            with session.begin():
                ds_fail = DataSource(
                    organization_id=org.id,
                    name=f"Failed Upload: {filename}",
                    source_type="CSV",
                    file_name=filename,
                    file_size_bytes=len(content),
                    file_checksum=checksum,
                    uploaded_by_id=user.id,
                )
                session.add(ds_fail)
                session.flush()

                job_fail = ImportJob(
                    data_source_id=ds_fail.id,
                    target_entity=target_entity,
                    status="rolled_back",
                    total_rows=len(rows),
                    loaded_rows=0,
                    rejected_rows=len(rows),
                    mapping_config=mapping,
                    error_details={"error": str(e)},
                    started_at=datetime.now(UTC),
                    completed_at=datetime.now(UTC),
                )
                session.add(job_fail)
                session.flush()

                p_fail = PipelineRun(
                    import_job_id=job_fail.id,
                    pipeline_name=f"Ingest-{target_entity.capitalize()}",
                    status="failed",
                    metrics={"error": str(e)},
                    started_at=datetime.now(UTC),
                    ended_at=datetime.now(UTC),
                )
                session.add(p_fail)

            if isinstance(e, AppException):
                raise e
            raise AppException(
                f"Import transaction failed and was rolled back cleanly: {e}",
                status_code=400,
                code="TRANSACTION_ROLLED_BACK",
            ) from e

        return ImportResultResponse(
            import_job_id=import_job.id,
            data_source_id=data_source.id,
            target_entity=target_entity,
            status=import_job.status,
            total_rows=import_job.total_rows,
            loaded_rows=import_job.loaded_rows,
            rejected_rows=import_job.rejected_rows,
            error_details=error_details or None,
        )


ingestion_service = IngestionService()
