import os
import polars as pl
import dotenv

import utils.AuditLogHelper as audit_helper
import utils.DirectoryGenerator as directory_generator
import utils.DataExtractor as data_extractor
import utils.DataTransformer as data_transformer


# Load environment variables
dotenv.load_dotenv()
directory_generator.generate_directories()

WORLD_BANK_URL = os.getenv("WORLD_BANK_URL")

# File paths
ROOT_DIR = os.getenv("ROOT_DIR")
RAW_GDP_DIR = os.path.join(ROOT_DIR, "raw", "gdp")
RAW_AUDIT_DIR = os.path.join(ROOT_DIR, "raw", "audit")

RAW_JSON_FILE = os.path.join(RAW_GDP_DIR, "gdp.json")
AUDIT_FILE = os.path.join(RAW_AUDIT_DIR, "ingestion_log.csv")

# Phase 2 output directories
STANDARDIZED_GDP_DIR = os.path.join(
    ROOT_DIR,
    "standardized",
    "gdp"
)

STANDARDIZED_ERRORS_DIR = os.path.join(
    ROOT_DIR,
    "standardized",
    "errors"
)

# Phase 3 output directory
CURATED_GROWTH_RATE_DIR = os.path.join(
    ROOT_DIR,
    "curated",
    "growth_rate"
)


try:
    # Call the World Bank API to get GDP data
    gdp_data = data_extractor.extract_all_data(
        WORLD_BANK_URL,
        RAW_JSON_FILE
    )

    # Phase 2: Clean and transform GDP data
    valid_df, error_df = data_transformer.transform_gdp(
        RAW_JSON_FILE,
        STANDARDIZED_GDP_DIR,
        STANDARDIZED_ERRORS_DIR
    )

    # Phase 3: Calculate GDP growth rate
    growth_df = data_transformer.calculate_growth_rate(
        STANDARDIZED_GDP_DIR,
        CURATED_GROWTH_RATE_DIR
    )

    data_frame = pl.DataFrame(gdp_data)

    row_count = len(gdp_data)

    # Log successful ingestion
    audit_helper.write_audit_log(
        audit_file=AUDIT_FILE,
        source=WORLD_BANK_URL,
        raw_file=RAW_JSON_FILE,
        status="SUCCESS",
        row_count=row_count
    )

    # Analyze the raw data
    unique_countries = data_frame.select(
        pl.col("countryiso3code").n_unique()
    ).item()

    earliest_year = data_frame.select(
        pl.col("date").min()
    ).item()

    latest_year = data_frame.select(
        pl.col("date").max()
    ).item()

    print("\n--------------------------------")
    print("Phase 1: Data Ingestion")
    print("Status: SUCCESS")
    print(f"Raw records: {row_count}")
    print(f"Unique ISO codes: {unique_countries}")
    print(f"Year range: {earliest_year}-{latest_year}")
    print(f"Raw output: {RAW_JSON_FILE}")
    print(f"Audit log: {AUDIT_FILE}")

    print("\n--------------------------------")
    print("Phase 2: Data Transformation")
    print(f"Raw records: {row_count}")
    print(f"Standardized records: {valid_df.height}")
    print(f"Rejected null records: {error_df.height}")
    print(
        f"Validation: {valid_df.height} + "
        f"{error_df.height} = {row_count}"
    )
    print(f"Standardized output: {STANDARDIZED_GDP_DIR}")
    print(
        "Error file: "
        f"{os.path.join(STANDARDIZED_ERRORS_DIR, 'gdp_null_errors.csv')}"
    )

    print("\n--------------------------------")
    print("Phase 3: GDP Growth Rate")
    print(f"Curated records: {growth_df.height}")
    print("Partitioned by: year")
    print(f"Curated output: {CURATED_GROWTH_RATE_DIR}")

    print("\nPhilippines GDP Growth Demonstration (2021-2025)")
    print(
        growth_df
        .filter(
            (pl.col("countryiso3code") == "PHL") &
            (pl.col("year").is_between(2021, 2025))
        )
        .sort("year")
    )


except Exception:
    # Log failed ingestion
    audit_helper.write_audit_log(
        audit_file=AUDIT_FILE,
        source=WORLD_BANK_URL,
        raw_file=RAW_JSON_FILE,
        status="FAILED",
        row_count=0
    )
    raise