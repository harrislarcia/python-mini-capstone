import os
import polars as pl


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

    print()
    print("--------------------------------")
    print("GDP Transformation")
    print(f"Raw records: {df.height}")
    print(f"Valid records: {valid_df.height}")
    print(f"Error records: {error_df.height}")
    print(f"Standardized output: {standardized_dir}")
    print(f"Error output: {error_file}")

    return valid_df, error_df