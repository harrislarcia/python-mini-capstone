import utils.DataExtractor as data_extractor
from unittest.mock import patch, MagicMock

def test_data_extractor(tmp_path):

    # Create a mock API response
    mock_response = MagicMock()

    mock_response.json.return_value = [
        {"pages": 1},  # metadata
        [
            {"country": "A", "value": 1000},
            {"country": "B", "value": 2000}
        ]  # page data
    ]

    mock_response.raise_for_status.return_value = None

    # Temporary output file for the test
    output_file = tmp_path / "output.json"

    # Mock requests.get()
    with patch(
        "utils.DataExtractor.req.get",
        return_value=mock_response
    ) as mock_get:

        result = data_extractor.extract_all_data(
            "http://fakeurl.com",
            str(output_file)
        )

    # Verify the returned data
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["country"] == "A"
    assert result[1]["value"] == 2000

    # Verify requests.get() was called correctly
    mock_get.assert_called_once_with(
        "http://fakeurl.com",
        params={
            "page": 1,
            "per_page": 1000
        },
        timeout=30
    )

    # Verify the output file was created
    assert output_file.exists()

def test_data_extractor_retry(tmp_path):
    # Create a mock successful API response
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"pages": 1},
        [
            {"country": "A", "gdp": 1000},
            {"country": "B", "gdp": 2000}
        ]
    ]
    mock_response.raise_for_status.return_value = None
    output_file = tmp_path / "output.json"

    # First request fails, second request succeeds
    with patch(
        "utils.DataExtractor.req.get",
        side_effect=[
            data_extractor.req.exceptions.RequestException("Connection error"),
            mock_response
        ]
    ) as mock_get:
        with patch("utils.DataExtractor.time.sleep") as mock_sleep:
            result = data_extractor.extract_all_data(
                "http://fakeurl.com",
                str(output_file)
            )

    # Verify the data was eventually extracted
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["country"] == "A"
    assert result[1]["gdp"] == 2000

    # Verify requests.get() was called twice
    assert mock_get.call_count == 2

    # Verify retry waited 3 seconds
    mock_sleep.assert_called_once_with(3)

    # Verify output file was created
    assert output_file.exists()