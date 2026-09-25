import json
import time
import requests as req

"""
    Fetches all data from the World Bank API and saves it to a JSON file.
    Used looping and pagination to retrieve all pages of data.
    Implements retry logic for failed requests.
"""

def extract_all_data(url, output_file):

    page = 1
    per_page = 1000
    max_retries = 3

    # Start with an empty JSON array
    all_data = []

    while True:
        for attempt in range(1, max_retries + 1):
            try:
                print(
                    f"Requesting page {page} "
                    f"(attempt {attempt}/{max_retries})..."
                )

                response = req.get(
                    url,
                    params={
                        "page": page,
                        "per_page": per_page
                    },
                    timeout=30
                )

                response.raise_for_status()
                data = response.json()
                break

            except req.exceptions.RequestException as e:
                print(
                    f"Request failed for page {page}: {e}"
                )
                
                if attempt == max_retries:
                    raise

                wait_time = 3

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

        metadata = data[0]
        page_data = data[1]

        total_pages = metadata["pages"]

        # Add current page to existing data
        all_data.extend(page_data)

        # Save immediately after every page
        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as json_file:

            json.dump(
                all_data,
                json_file,
                indent=2
            )

        print(
            f"Extracted page {page}/{total_pages} "
            f"({len(page_data)} records)"
        )

        print(
            f"Saved {len(all_data)} total records"
        )

        if page >= total_pages:
            break

        page += 1

    return all_data