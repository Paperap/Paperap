"""

The integration testing framework gathers sample data in a better way than this script,
but in case it's needed in the future, I'm leaving it here for now.

 ----------------------------------------------------------------------------

    METADATA:

        File:    create_samples.py
        Project: paperap
        Created: 2025-03-11
        Version: 0.0.9
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-21     By Jess Mann

"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = os.getenv("PAPERLESS_BASE_URL").rstrip("/") + "/api/"
TOKEN = os.getenv("PAPERLESS_TOKEN")
SAVE_DIR = Path("tests/sample_data")
HEADERS = {"Authorization": f"Token {TOKEN}"}

# Ensure save directory exists
SAVE_DIR.mkdir(parents=True, exist_ok=True)


def fetch_api_root() -> Dict[str, Any]:
    response = requests.get(API_BASE_URL, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def fetch_endpoint_data(endpoint_name: str, endpoint_url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    params = params or {}
    try:
        response = requests.get(endpoint_url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        save_file(endpoint_name, "list", data)
        return data
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {endpoint_name}: {e}")
        return {}


def fetch_item_data(endpoint_name: str, item_url: str) -> None:
    try:
        response = requests.get(item_url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        save_file(endpoint_name, "item", data)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch item for {endpoint_name}: {e}")


def fetch_raw_data(endpoint_name: str, endpoint_url: str, params: Dict[str, Any] = None) -> None:
    # Used for endpoints returning non-JSON (e.g. binary downloads)
    params = params or {}
    try:
        response = requests.get(endpoint_url, headers=HEADERS, params=params)
        response.raise_for_status()
        # Save the raw content along with headers for inspection
        data = {
            "content": response.content.decode("utf-8", errors="replace"),
            "headers": dict(response.headers),
        }
        save_file(endpoint_name, "item", data)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch raw data for {endpoint_name}: {e}")


def save_file(endpoint_name: str, suffix: str, data: Any) -> None:
    filename = SAVE_DIR / f"{endpoint_name}_{suffix}.json"
    with filename.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
    logger.debug(f"Saved sample data for {endpoint_name} ({suffix}) to {filename}")


def fetch_document_related_samples(document_id: int) -> None:
    endpoints = {
        "document_download": f"{API_BASE_URL}document/{document_id}/download/",
        "document_preview": f"{API_BASE_URL}document/{document_id}/preview/",
        "document_thumbnail": f"{API_BASE_URL}document/{document_id}/thumb/",
        "document_metadata": f"{API_BASE_URL}document/{document_id}/metadata/",
        "document_notes": f"{API_BASE_URL}document/{document_id}/notes/",
        "document_suggestions": f"{API_BASE_URL}document/{document_id}/suggestions/",
    }

    # For download/preview/thumbnail, assume binary data and save raw (decoded as text for inspection)
    for key in ["document_download", "document_preview", "document_thumbnail"]:
        fetch_raw_data(key, endpoints[key], params={"original": "false"})

    # For metadata, notes, suggestions, assume JSON responses
    for key in ["document_metadata", "document_notes", "document_suggestions"]:
        try:
            response = requests.get(endpoints[key], headers=HEADERS)
            response.raise_for_status()
            data = response.json()
            save_file(key, "item", data)
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {key}: {e}")

    # Fetch next_asn endpoint (returns JSON with next_asn)
    next_asn_url = f"{API_BASE_URL}document/next_asn/"
    try:
        response = requests.get(next_asn_url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        save_file("document_next_asn", "item", data)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch document_next_asn: {e}")


def main() -> None:
    logger.info("Fetching API root...")
    api_root = fetch_api_root()

    sample_document_id = None

    # Process each endpoint returned by the API root.
    for endpoint, url in api_root.items():
        if isinstance(url, str) and url.startswith("http"):
            logger.info(f"Fetching sample data from endpoint '{endpoint}'...")
            data = fetch_endpoint_data(endpoint, url, params={"page_size": 1})
            # If a list with items is returned, fetch a sample item.
            if isinstance(data, dict) and data.get("results"):
                first_item = data["results"][0]
                # Try to use the 'url' field in the item; if not available, build one using API_BASE_URL and item id.
                item_url = first_item.get("url")
                if not item_url and "id" in first_item:
                    item_url = f"{url.rstrip('/')}/{first_item['id']}/"
                if item_url:
                    fetch_item_data(endpoint, item_url)
                    # Save a sample document id for later use if the endpoint is "documents"
                    if endpoint == "documents" and not sample_document_id:
                        sample_document_id = first_item.get("id")
            else:
                logger.info(f"No list items found for endpoint '{endpoint}'.")

    # Fetch additional endpoints that are not directly in the API root but are documented.
    if sample_document_id:
        logger.info(f"Fetching additional document-related endpoints using document id {sample_document_id}...")
        fetch_document_related_samples(sample_document_id)
    else:
        logger.warning("No sample document found; skipping document-related endpoints.")

    # Additional endpoints
    extra_endpoints = {
        "users_me": f"{API_BASE_URL}users/me/",
        "profile": f"{API_BASE_URL}profile/",
        "saved_views": f"{API_BASE_URL}saved_views/",
        "share_links": f"{API_BASE_URL}share_links/",
        "storage_paths": f"{API_BASE_URL}storage_paths/",
        "tasks": f"{API_BASE_URL}tasks/",
        "ui_settings": f"{API_BASE_URL}ui_settings/",
        "workflows": f"{API_BASE_URL}workflows/",
        "workflow_triggers": f"{API_BASE_URL}workflow_triggers/",
        "workflow_actions": f"{API_BASE_URL}workflow_actions/",
    }

    for key, url in extra_endpoints.items():
        logger.info(f"Fetching extra endpoint '{key}'...")
        fetch_endpoint_data(key, url, params={"page_size": 1})
        # Attempt to fetch an item if available.
        data = fetch_api_root_item(url)
        if data and "id" in data:
            fetch_item_data(key, f"{url.rstrip('/')}/{data['id']}/")

    logger.info("Data collection complete.")


def fetch_api_root_item(url: str) -> Dict[str, Any] | None:
    """
    Try to fetch one item from the endpoint by using page_size=1.
    Returns the first item if available.
    """
    try:
        response = requests.get(url, headers=HEADERS, params={"page_size": 1})
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and data.get("results"):
            return data["results"][0]
    except requests.RequestException as e:
        logger.error(f"Failed to fetch item from {url}: {e}")
    return None


if __name__ == "__main__":
    main()
