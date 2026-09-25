import csv
import utils.AuditLogHelper as audit_log_helper


def test_write_audit_log_creates_file(tmp_path):

    audit_file = tmp_path / "ingestion_log.csv"

    audit_log_helper.write_audit_log(
        audit_file=str(audit_file),
        source="World Bank API",
        raw_file="gdp.json",
        status="SUCCESS",
        row_count=100,
        error=""
    )

    # Verify the file was created
    assert audit_file.exists()

    # Read the CSV and verify its contents
    with open(
        audit_file,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        rows = list(csv.reader(file))

    # Verify header
    assert rows[0] == [
        "timestamp",
        "status",
        "source",
        "row_count",
        "file",
        "error"
    ]

    # Verify audit record
    assert rows[1][1] == "SUCCESS"
    assert rows[1][2] == "World Bank API"
    assert rows[1][3] == "100"
    assert rows[1][4] == "gdp.json"
    assert rows[1][5] == ""
