import os
import polars as pl


# ============= Phase 2 =============

def transform_gdp(input_file, standardized_dir, error_dir):
    """
    Clean and transform raw World Bank GDP data.

    - Reads the raw JSON file.
    - Flattens the country Struct.
    - Renames date to year and value to gdp.
    - Removes rows where GDP is null.
    - Saves null GDP rows as a CSV error file.
    - Writes valid data as partitioned Parquet files by year.
    """

    # Read raw JSON
    df = pl.read_json(input_file)

    # Flatten the nested country Struct
    df = df.with_columns(
        pl.col("country")
        .struct.field("value")
        .alias("country")
    )

    # Rename columns
    df = df.rename({
        "date": "year",
        "value": "gdp"
    })

    # Convert year to integer
    df = df.with_columns(
        pl.col("year").cast(pl.Int32)
    )

    # Keep only the standardized GDP columns
    df = df.select([
        "countryiso3code",
        "country",
        "year",
        "gdp"
    ])

    # Separate rows where GDP is null
    error_df = df.filter(
        pl.col("gdp").is_null()
    )

    valid_df = df.filter(
        pl.col("gdp").is_not_null()
    )

    # Create directories if they don't exist
    os.makedirs(standardized_dir, exist_ok=True)
    os.makedirs(error_dir, exist_ok=True)

    # Save rows with missing GDP
    error_file = os.path.join(
        error_dir,
        "gdp_null_errors.csv"
    )

    error_df.write_csv(error_file)

    # Write valid GDP data as partitioned Parquet
    valid_df.write_parquet(
        standardized_dir,
        use_pyarrow=True,
        pyarrow_options={
            "partition_cols": ["year"]
        }
    )

    return valid_df, error_df


# ============= Phase 3 =============

def calculate_growth_rate(standardized_dir, curated_dir):
    """
    Calculate year-on-year GDP growth rate for each country.
    """

    # Read Hive-partitioned Parquet data
    df = pl.read_parquet(
        os.path.join(standardized_dir, "**", "*.parquet"),
        hive_partitioning=True
    )

    # Sort by country and year
    df = df.sort([
        "countryiso3code",
        "year"
    ])

    # Get previous year's GDP and year for each country
    df = df.with_columns([
        pl.col("gdp")
        .shift(1)
        .over("countryiso3code")
        .alias("previous_gdp"),

        pl.col("year")
        .shift(1)
        .over("countryiso3code")
        .alias("previous_year")
    ])

    # Calculate YoY GDP growth rate
    df = df.with_columns(
        pl.when(
            pl.col("previous_year") == pl.col("year") - 1
        )
        .then(
            (
                (pl.col("gdp") - pl.col("previous_gdp"))
                / pl.col("previous_gdp")
            ) * 100
        )
        .otherwise(None)
        .alias("growth_rate")
    )

    # Keep curated columns
    df = df.select([
        "countryiso3code",
        "country",
        "year",
        "gdp",
        "previous_gdp",
        "growth_rate"
    ])

    # Create output directory
    os.makedirs(curated_dir, exist_ok=True)

    # Write curated data as partitioned Parquet
    df.write_parquet(
        curated_dir,
        use_pyarrow=True,
        pyarrow_options={
            "partition_cols": ["year"]
        }
    )

    return df