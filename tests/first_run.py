"""

Usage: python -m tests.first_run

"""

from __future__ import annotations

import json
import logging
import os
import random
import re
import tempfile
from pathlib import Path
from typing import Any, List
import sys
import requests
from alive_progress import alive_bar, alive_it
from dotenv import load_dotenv
from faker import Faker

from paperap.client import PaperlessClient
from paperap.exceptions import PaperapError
from paperap.models import *
from paperap.resources import *

from .create_samples import SampleDataCollector
from .lib import factories

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize faker for content generation
fake = Faker()

SAMPLE_DATA = Path(__file__).parent / "sample_data"

def generate_sample_text_files(output_dir: Path, count: int = 20) -> list[Path]:
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

    # Note: This function is now called from a context with an existing
    # progress bar, so we don't create a new one here
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

        print(f"This will delete all data in the {self.client.base_url} server. Do you want to continue? Type 'delete everything' to continue.")

        confirmation = input()
        if confirmation.lower() != 'delete everything':
            logger.info("Cleanup operation cancelled.")
            sys.exit(1)

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
        # Calculate total steps for progress bar
        total_steps = (
            len(self.factories) +  # Creating models
            2 +                   # Sample documents
            20 +                 # Text files generation
            20 +                 # Text files upload
            102                   # Wait for tasks (2 samples + 20 text files)
        )

        # Create a single progress bar for the entire process
        with alive_bar(total_steps, title="Setting up test environment", enrich_print=True) as bar:
            basic = {"owner": 1, "id": 0}
            upload_tasks = []

            # Create sample data for every model registered in the factories dictionary
            bar.text("Creating sample models...")
            logger.info("Creating sample models...")
            for key, (model_class, factory) in self.factories.items():
                logger.debug(f"Creating sample data for {key}...")
                self.create_models(key, model_class, factory, **basic)
                bar()

            # Upload sample documents
            bar.text("Uploading sample documents...")
            logger.info("Uploading sample documents...")
            documents = [
                SAMPLE_DATA / "uploads" / "Sample JPG.jpg",
                SAMPLE_DATA / "uploads" / "Sample PDF.pdf",
            ]
            for filename in documents:
                try:
                    task_id = self.client.documents.upload_async(filename)
                    upload_tasks.append(task_id)
                    logger.debug("Uploaded document %s, task ID: %s", filename, task_id)
                except PaperapError as e:
                    logger.warning("Failed to upload document %s: %s", filename, e)
                bar()

            # Generate text files
            bar.text("Generating sample text files...")
            logger.info("Generating sample text files...")
            with tempfile.TemporaryDirectory() as text_files_dir:
                text_files = []
                for i in range(1, 21):  # Generate 20 files
                    bar.text(f"Generating text file {i}/20...")

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
                    file_path = Path(text_files_dir) / "sample_text_files" / filename

                    # Create directory if it doesn't exist
                    file_path.parent.mkdir(parents=True, exist_ok=True)

                    # Write content to file
                    with file_path.open("w", encoding="utf-8") as f:
                        f.write(content)

                    text_files.append(file_path)
                    bar()

                # Upload the text files
                bar.text("Uploading text files...")
                logger.info("Uploading text files...")
                for i, filename in enumerate(text_files):
                    bar.text(f"Uploading text file {i+1}/{len(text_files)}...")
                    try:
                        task_id = self.client.documents.upload_async(filename)
                        upload_tasks.append(task_id)
                        logger.debug("Started upload for text document %s, task ID: %s", filename, task_id)
                    except PaperapError as e:
                        logger.warning("Failed to upload document %s: %s", filename, e)
                    bar()

            # Wait for all tasks to complete
            if upload_tasks:
                bar.text(f"Waiting for {len(upload_tasks)} upload tasks to complete...")
                logger.info(f"Waiting for {len(upload_tasks)} upload tasks to complete...")
                task_resource = TaskResource(client=self.client)

                def on_task_success(task):
                    logger.debug(f"Task {task.id} completed successfully")

                def on_task_failure(task):
                    logger.warning(f"Task {task.id} failed: {task.status_str}")

                for i, task_id in enumerate(upload_tasks):
                    bar.text(f"Monitoring task {i+1}/{len(upload_tasks)}...")
                    task_resource.wait_for_task(
                        task_id,
                        success_callback=on_task_success,
                        failure_callback=on_task_failure
                    )
                    bar()

def main() -> None:
    logger.info("Starting Paperless first run configuration...")

    # Create just one manager and collector instance
    manager = PaperlessManager()
    collector = SampleDataCollector()

    # Cleanup phase
    logger.info("Cleaning up existing data...")
    manager.cleanup()

    # Upload phase - has its own progress bar
    logger.info("Uploading test data...")
    manager.upload()

    # Collection phase
    logger.info("Collecting sample API data...")
    collector.run()

    logger.info("First run setup completed successfully!")

if __name__ == "__main__":
    main()
