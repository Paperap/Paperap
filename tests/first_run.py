"""

Usage: python -m tests.first_run


 ----------------------------------------------------------------------------

    METADATA:

        File:    first_run.py
        Project: paperap
        Created: 2025-03-21
        Version: 0.0.10
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-21     By Jess Mann

"""

from __future__ import annotations
import tempfile
import json
import logging
import os
import re
import random
from pathlib import Path
from typing import Any, List

from faker import Faker
from alive_progress import alive_bar

import requests
from dotenv import load_dotenv

from paperap.client import PaperlessClient
from paperap.models import *
from paperap.resources import *
from paperap.exceptions import PaperapError
from .create_samples import SampleDataCollector
from .lib import factories

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize faker for content generation
fake = Faker()

SAMPLE_DATA = Path(__file__).parent / "sample_data"

def generate_sample_text_files(output_dir: Path, count: int = 100) -> List[Path]:
    """
    Generate sample text files for document upload testing.
    
    Args:
        output_dir: Directory to save the files in
        count: Number of files to generate
        
    Returns:
        List of paths to the generated files
    """
    # Create the output directory if it doesn't exist
    sample_dir = output_dir / "sample_text_files"
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    with alive_bar(count, title="Generating sample text files") as bar:
        for i in range(1, count + 1):
            # Generate content: 1-3 paragraphs of text
            num_paragraphs = random.randint(1, 3)
            paragraphs = [fake.paragraph(nb_sentences=random.randint(3, 8)) for _ in range(num_paragraphs)]
            content = "\n\n".join(paragraphs)
            
            # Add some metadata at the top of some files
            if random.random() < 0.3:  # 30% chance
                metadata = [
                    f"Title: {fake.sentence(nb_words=random.randint(3, 6)).rstrip('.')}",
                    f"Date: {fake.date()}",
                    f"Author: {fake.name()}",
                    f"Subject: {fake.bs()}"
                ]
                content = "\n".join(metadata) + "\n\n" + content
            
            # Create a filename with a pattern 
            filename = f"sample_{i:03d}_{fake.word()}.txt"
            file_path = sample_dir / filename
            
            # Write content to file
            with file_path.open("w", encoding="utf-8") as f:
                f.write(content)
                
            generated_files.append(file_path)
            bar()
            
    logger.info(f"Generated {count} sample text files in {sample_dir}")
    return generated_files

class PaperlessManager:
    """
    Manages Paperless-related operations, including loading sample data, creating entities,
    and cleaning up test data.
    """

    def __init__(self) -> None:
        self.client = PaperlessClient()

        # Register factories for every model exposed by paperless-ngx
        self.factories = {
            "correspondents": (Correspondent, factories.CorrespondentFactory),
            "document_types": (DocumentType, factories.DocumentTypeFactory),
            "tags": (Tag, factories.TagFactory),
            "custom_fields": (CustomField, factories.CustomFieldFactory),
            "storage_paths": (StoragePath, factories.StoragePathFactory),
            #"saved_views": (SavedView, factories.SavedViewFactory),
            #"share_links": (ShareLinks, factories.ShareLinksFactory),
            #"groups": (Group, factories.GroupFactory),
            #"workflows": (Workflow, factories.WorkflowFactory),
            #"workflow_triggers": (WorkflowTrigger, factories.WorkflowTriggerFactory),
            #"workflow_actions": (WorkflowAction, factories.WorkflowActionFactory),
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
            DocumentResource,
            CorrespondentResource,
            DocumentTypeResource,
            TagResource,
            CustomFieldResource,
            StoragePathResource,
            SavedViewResource,
            ShareLinksResource,
            GroupResource,
            WorkflowResource,
            WorkflowTriggerResource,
            WorkflowActionResource,
        ]
        for resource_cls in resources:
            resource = resource_cls(client=self.client)
            for model in list(resource.all()):
                try:
                    model.delete()
                    logger.debug(f"Deleted {model}")
                except PaperapError as e:
                    logger.warning("Failed to delete %s: %s", model, e)

        self.client.documents.empty_trash()

    def create_models(self, name: str, model_class: StandardModel, factory: factories.PydanticFactory, *, _number: int = 76, **kwargs: Any) -> None:
        for i in range(_number):
            try:
                data = factory.create_api_data(**kwargs)
                # If data includes a name, append something to it to ensure it is unique
                if "name" in data:
                    data["name"] = f"{data['name']} {i}"
                model = model_class.create(_relationships=False, **data)
                logger.debug("Created %s with ID %s", name, model.id)
            except PaperapError as e:
                logger.warning("Failed to create %s: %s", name, e)

    def upload(self) -> None:
        basic = {"owner": 1, "id": 0}

        # Create sample data for every model registered in the factories dictionary.
        for key, (model_class, factory) in self.factories.items():
            logger.debug(f"Creating sample data for {key}...")
            self.create_models(key, model_class, factory, **basic)

        # Upload sample documents
        documents = [
            SAMPLE_DATA / "uploads" / "Sample JPG.jpg",
            SAMPLE_DATA / "uploads" / "Sample PDF.pdf",
        ]
        for filename in documents:
            try:
                document = self.client.documents.upload_sync(filename)
                logger.debug("Uploaded document %s", document.id)
            except PaperapError as e:
                logger.warning("Failed to upload document %s: %s", filename, e)
                
        # Generate and upload text files
        logger.info("Generating and uploading sample text files...")
        with tempfile.TemporaryDirectory() as text_files_dir:
            text_files = generate_sample_text_files(text_files_dir)
            
            # Upload a subset of the generated text files (first 20 to avoid overloading)
            with alive_bar(len(text_files), title="Uploading text files") as bar:
                for filename in text_files:
                    try:
                        document = self.client.documents.upload_sync(filename)
                        logger.debug("Uploaded text document %s", document.id)
                        bar()
                    except PaperapError as e:
                        logger.warning("Failed to upload document %s: %s", filename, e)
                        bar()

def main() -> None:
    manager = PaperlessManager()
    manager.cleanup()
    manager.upload()
    collector = SampleDataCollector()
    collector.run()

if __name__ == "__main__":
    main()
