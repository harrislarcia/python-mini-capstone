import json
import polars as pl

import utils.DataTransformer as data_transformer


def test_transform_gdp(tmp_path):
    # Create temporary raw JSON file
    input_file = tmp_path / "gdp.json"

    raw_data = [
        {
            "countryiso3code": "PHL",
            "country": {
                "id": "PH",
                "value": "Philippines"
            },
            "date": "2023",
            "value": 400000000000
        },
        {
            "countryiso3code": "PHL",
            "country": {
                "id": "PH",
                "value": "Philippines"
            },
            "date": "2022",
            "value": None
        }
    ]

    with open(
        input_file,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(raw_data, file)

    standardized_dir = tmp_path / "standardized"
    error_dir = tmp_path / "errors"

    valid_df, error_df = data_transformer.transform_gdp(
        str(input_file),
        str(standardized_dir),
        str(error_dir)
    )

    # Verify flattened country
    assert valid_df["country"][0] == "Philippines"

    # Verify renamed columns
    assert valid_df.columns == [
        "countryiso3code",
        "country",
        "year",
        "gdp"
    ]

    # Verify year was converted to integer
    assert valid_df["year"].dtype == pl.Int32

    # Verify GDP value
    assert valid_df["gdp"][0] == 400000000000

    # Verify error row contains the null GDP
    assert error_df["gdp"][0] is None

    # Verify error CSV was created
    error_file = error_dir / "gdp_null_errors.csv"
    assert error_file.exists()

    # Verify standardized directory was created
    assert standardized_dir.exists()

def test_calculate_growth_rate(tmp_path):

    standardized_dir = tmp_path / "standardized"
    curated_dir = tmp_path / "curated"

    standardized_dir.mkdir()

    # Create test GDP data
    df = pl.DataFrame({
        "countryiso3code": [
            "PHL",
            "PHL",
            "PHL"
        ],
        "country": [
            "Philippines",
            "Philippines",
            "Philippines"
        ],
        "year": [
            2021,
            2022,
            2023
        ],
        "gdp": [
            100.0,
            110.0,
            121.0
        ]
    })

    # Write as partitioned Parquet
    df.write_parquet(
        standardized_dir,
        use_pyarrow=True,
        pyarrow_options={
            "partition_cols": ["year"]
        }
    )

    result = data_transformer.calculate_growth_rate(
        str(standardized_dir),
        str(curated_dir)
    )

    # Verify previous GDP
    assert result["previous_gdp"].to_list() == [
        None,
        100.0,
        110.0
    ]

    # 2021 has no previous year
    assert result["growth_rate"][0] is None

    # 2022:
    # ((110 - 100) / 100) * 100 = 10%
    assert result["growth_rate"][1] == 10.0

    # 2023:
    # ((121 - 110) / 110) * 100 = 10%
    assert result["growth_rate"][2] == 10.0

    # Verify curated directory was created
    assert curated_dir.exists()