import os
import csv
from datetime import datetime, timezone

"""
    Audit Log Helper to write audit logs for the data ingestion process.
"""

def write_audit_log(
    audit_file,
    source,
    raw_file,
    status,
    row_count,
    error=""
):
    file_exists = os.path.exists(audit_file)

    with open(
        audit_file,
        "a",
        newline="",
        encoding="utf-8"
    ) as audit_file_handle:

        writer = csv.writer(audit_file_handle)

        if not file_exists:
            writer.writerow([
                "timestamp",
                "status",
                "source",
                "row_count",
                "file",
                "error"
            ])

        writer.writerow([
            datetime.now(timezone.utc).isoformat(),
            status,
            source,
            row_count,
            raw_file,
            error
        ])