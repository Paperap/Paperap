"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    first_run.py
        Project: paperap
        Created: 2025-03-20
        Version: 0.0.9
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
import re
from paperap.client import PaperlessClient
from paperap.models import *
from paperap.resources import *
from paperap.exceptions import PaperapError
from . import create_samples
from .lib import factories

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SAMPLE_DATA = Path(__file__).parent / "sample_data"

class PaperlessManager:
    """
    Manages Paperless-related operations, including loading sample data, creating entities,
    and cleaning up test data.
    """

    def __init__(self) -> None:
        self.client = PaperlessClient()

        self.factories = {
            "correspondents": (Correspondent, factories.CorrespondentFactory),
            "document_types": (DocumentType, factories.DocumentTypeFactory),
            "tags": (Tag, factories.TagFactory),
        }

    def cleanup(self) -> None:
        """
        Deletes test entities from Paperless while handling errors gracefully.
        """
        if not re.match(r"https?://(192.168|10.|127.0.0|0.0.0|localhost)", str(self.client.base_url)):
            logger.error(f"Refusing to delete data from a non-local server: {self.client.base_url}")
            return

        """
        print(f"This will delete all data in the {self.client.base_url} server. Do you want to continue? Type 'delete everything' to continue.")

        confirmation = input()
        if confirmation.lower() != 'delete everything':
            logger.info("Cleanup operation cancelled.")
            return
        """

        resources = [
            DocumentResource, CorrespondentResource, DocumentTypeResource, 
            TagResource, CustomFieldResource, StoragePathResource, SavedViewResource,
        ]
        for resource in resources:
            for model in list(resource(client=self.client).all()):
                try:
                    model.delete()
                except PaperapError as e:
                    logger.warning("Failed to delete %s: %s", model, e)

    def create_models(self, name : str, model_class : StandardModel, factory : factories.PydanticFactory, *, _number : int = 76, **kwargs : Any) -> None:
        for i in range(_number):
            try:
                data = factory.create_api_data(**kwargs)
                model = model_class.create(_relationships=False, **data)
                logger.debug("Created %s with ID %s", name, model.id)
            except PaperapError as e:
                logger.warning("Failed to create %s: %s", name, e)

    def upload(self) -> None:
        """
        Creates test entities in Paperless while handling errors gracefully.
        """
        basic = {"owner": 1, "id": 0}
        # Note: some of these models won't be created due to name:owner being unique
        self.create_models("correspondents", Correspondent, factories.CorrespondentFactory, **basic)
        self.create_models("document_types", DocumentType, factories.DocumentTypeFactory, **basic)
        self.create_models("tags", Tag, factories.TagFactory, **basic)
        #self.create_models("custom_fields", CustomField, factories.CustomFieldFactory, id=0)
        #self.create_models("storage_paths", StoragePath, factories.StoragePathFactory, **basic)
        #self.create_models("saved_view", SavedView, factories.SavedViewFactory, **basic)

        # Upload 2 sample documents
        documents = [
            SAMPLE_DATA / "uploads" / "Sample JPG.jpg",
            SAMPLE_DATA / "uploads" / "Sample PDF.pdf",
        ]
        for document in documents:
            try:
                self.client.documents.upload(document)
                logger.debug("Uploaded document %s", document)
            except PaperapError as e:
                logger.warning("Failed to upload document %s: %s", document, e)

    # TODO: Document note, Workflows, User, Group, UISettings, Task, ShareLinks, Profile

def main() -> None:
    manager = PaperlessManager()
    manager.cleanup()
    manager.upload()
    create_samples.main()


if __name__ == "__main__":
    main()
