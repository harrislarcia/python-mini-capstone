# World Bank GDP Pipeline Flow

## Phase 1: Data Ingestion

1. Request GDP data from the World Bank API in JSON format.
2. Use pagination to download the data in smaller pages.
3. Save 17,490 raw records to `world_bank_gdp_data/raw/gdp/gdp.json`.
4. Record the status, timestamp, source, row count, and file in `world_bank_gdp_data/raw/audit/ingestion_log.csv`.

JSON was selected because the API returns structured JSON directly.

## Phase 2: Data Transformation

1. Read the raw JSON with Polars.
2. Flatten the country field and rename `date` to `year` and `value` to `gdp`.
3. Separate valid GDP records from records with null GDP values.
4. Save 14,745 valid records as Parquet in `world_bank_gdp_data/standardized/gdp`.
5. Save 2,745 rejected records to `world_bank_gdp_data/standardized/errors/gdp_null_errors.csv`.

Validation: 14,745 valid + 2,745 rejected = 17,490 raw records.

## Phase 3: GDP Growth Rate

1. Read the standardized Parquet data.
2. Sort the records by country and year.
3. Use a Polars window function to obtain each country's previous-year GDP.
4. Calculate year-on-year growth:

   `((current GDP - previous GDP) / previous GDP) * 100`

5. Save 14,745 curated records to `world_bank_gdp_data/curated/growth_rate`.
6. Display Philippines results for 2021-2025 as a demonstration.

## Partition Strategy

Standardized and curated Parquet data are partitioned by `year`. This organizes period-based data and allows queries to read only the required year partitions.