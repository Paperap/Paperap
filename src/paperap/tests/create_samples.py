"""

The integration testing framework gathers sample data in a better way than this script,
but in case it's needed in the future, I'm leaving it here for now.

 ----------------------------------------------------------------------------

    METADATA:

        File:    create_samples.py
        Project: paperap
        Created: 2025-03-11
        Version: 0.0.5
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-11     By Jess Mann

"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

# Configuration
API_BASE_URL = os.getenv("PAPERLESS_BASE_URL") + "/api/" # type: ignore
TOKEN = os.getenv("PAPERLESS_TOKEN")
SAVE_DIR = Path("tests/sample_data")
# token auth
HEADERS = {"Authorization": f"Token {TOKEN}"}

# Ensure save directory exists
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def fetch_api_root():
    """Fetch the API root to determine available endpoints."""
    response = requests.get(API_BASE_URL, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def fetch_endpoint_data(endpoint_name, endpoint_url) -> None:
    """Fetch a sample from the given endpoint and save the response to a file."""
    try:
        response = requests.get(endpoint_url, headers=HEADERS, params={"page_size": 1})  # Limit to 1 item
        response.raise_for_status()
        data = response.json()

        # Save response to file
        filename = SAVE_DIR / f"{endpoint_name}_list.json"
        if filename.exists():
            logging.warning(f"Skip overwriting existing sample data for {endpoint_name}")
            return

        with filename.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        logging.info(f"Saved sample data for {endpoint_name} to {filename}")

    except requests.RequestException as e:
        logging.error(f"Failed to fetch {endpoint_name}: {e}")

def main() -> None:
    """Main function to extract and store API data."""
    logging.info("Fetching API root...")
    api_root = fetch_api_root()

    for endpoint, url in api_root.items():
        if isinstance(url, str) and url.startswith("http"):
            logging.info(f"Fetching sample data from {endpoint}...")
            fetch_endpoint_data(endpoint, url)

    logging.info("Data collection complete.")

if __name__ == "__main__":
    main()
