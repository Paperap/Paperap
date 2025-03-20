"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    first_run.py
        Project: paperap
        Created: 2025-03-20
        Version: 0.0.8
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-20     By Jess Mann

"""
from pathlib import Path
import json
import logging
from typing import Any, Dict, List, Type

from paperap.client import PaperlessClient
from paperap.models import Correspondent, DocumentType, Tag
from paperap.exceptions import PaperapError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PaperlessManager:
    """
    Manages Paperless-related operations, including loading sample data, creating entities,
    and cleaning up test data.
    """

    def __init__(self) -> None:
        self.client = PaperlessClient()

        self.SAMPLE_FILES = {
            "correspondents": ("correspondents_item.json", Correspondent, self.client.correspondents),
            "document_types": ("document_types_item.json", DocumentType, self.client.document_types),
            "tags": ("tags_item.json", Tag, self.client.tags),
        }

    @staticmethod
    def load_sample_data(filename: str) -> Dict[str, Any]:
        """
        Load sample data from a JSON file.
        
        Args:
            filename: The name of the file to load.

        Returns:
            A dictionary containing the sample data.
        """
        sample_data_filepath = Path(__file__).parent / "sample_data" / filename
        try:
            with open(sample_data_filepath, "r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error("Failed to load sample data from %s: %s", filename, e)
            return {}

    def cleanup(self) -> None:
        """
        Deletes test entities from Paperless while handling errors gracefully.
        """
        for name, (filename, model, manager) in self.SAMPLE_FILES.items():
            data = self.load_sample_data(filename)
            if not data:
                continue
            try:
                manager.delete(data["id"])
                logger.info("Deleted %s with ID %s", name, data["id"])
            except PaperapError as e:
                logger.warning("Failed to delete %s: %s", name, e)

    def upload(self) -> None:
        """
        Creates test entities in Paperless while handling errors gracefully.
        """
        for name, (filename, model, manager) in self.SAMPLE_FILES.items():
            data = self.load_sample_data(filename)
            if not data:
                continue
            try:
                instance = model.create(**data)
                logger.info("Created %s with ID %s", name, instance.id)
            except PaperapError as e:
                logger.warning("Failed to create %s: %s", name, e)

        # Upload 2 sample documents
        documents = [
            Path(__file__).parent / "sample_data" / "Sample JPG.jpg",
            Path(__file__).parent / "sample_data" / "Sample PDF.pdf",
        ]
        for document in documents:
            try:
                self.client.documents.upload(document)
                logger.info("Uploaded document %s", document)
            except PaperapError as e:
                logger.warning("Failed to upload document %s: %s", document, e)


def main() -> None:
    manager = PaperlessManager()
    manager.cleanup()
    manager.upload()


if __name__ == "__main__":
    main()
