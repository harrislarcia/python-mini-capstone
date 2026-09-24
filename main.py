import os
import polars as pl
import dotenv

import utils.AuditLogHelper as audit_helper
import utils.DirectoryGenerator as directory_generator
import utils.DataExtractor as data_extractor

# Load environment variables
dotenv.load_dotenv()
directory_generator.generate_directories()

WORLD_BANK_URL = os.getenv("WORLD_BANK_URL")

# File paths
ROOT_DIR = os.getenv("ROOT_DIR")
RAW_GDP_DIR = os.path.join(ROOT_DIR, "raw", "gdp")
RAW_AUDIT_DIR = os.path.join(ROOT_DIR, "raw", "audit")

STANDARDIZED_GDP_DIR = os.path.join(ROOT_DIR, "standardized", "gdp")

RAW_JSON_FILE = os.path.join(RAW_GDP_DIR, "gdp.json")
AUDIT_FILE = os.path.join(RAW_AUDIT_DIR, "ingestion_log.csv")
PARQUET_FILE = os.path.join(STANDARDIZED_GDP_DIR, "gdp.parquet")

try:
    # Call the World Bank API to get GDP data
    gdp_data = data_extractor.extract_all_data(
        WORLD_BANK_URL,
        RAW_JSON_FILE
    )

    data_frame = pl.DataFrame(gdp_data)

    data_frame.write_parquet(
        PARQUET_FILE
    )
    row_count = len(gdp_data)

    audit_helper.write_audit_log(
        audit_file=AUDIT_FILE,
        source=WORLD_BANK_URL,
        raw_file=RAW_JSON_FILE,
        status="SUCCESS",
        row_count=row_count
    )

    # Analyze the data
    unique_countries = data_frame.select(
        pl.col("countryiso3code").n_unique()
    ).item()

    unique_years = data_frame.select(
        pl.col("date").n_unique()
    ).item()

    earliest_year = data_frame.select(
        pl.col("date").min()
    ).item()

    latest_year = data_frame.select(
        pl.col("date").max()
    ).item()

    print()
    print("--------------------------------")
    print("Raw GDP Data Analysis")
    print(f"Total records: {row_count}")
    print(f"Countries Available: {unique_countries}")
    print(f"Earliest year: {earliest_year}")
    print(f"Latest year: {latest_year}")
    print(f"Number of years: {unique_years}")

except Exception as e:
    # Log failure
    audit_helper.write_audit_log(
        audit_file=AUDIT_FILE,
        source=WORLD_BANK_URL,
        raw_file=RAW_JSON_FILE,
        status="SUCCESS",
        row_count=row_count
    )