"""
Provide specialized querysets for interacting with Paperless-NGX workflow resources.

This module contains queryset implementations for workflows, workflow actions, and
workflow triggers. Each queryset extends the standard queryset functionality with
specialized filtering methods specific to workflow-related resources.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Self

from paperap.models.abstract.queryset import BaseQuerySet, StandardQuerySet

if TYPE_CHECKING:
    from paperap.models.workflow.model import Workflow, WorkflowAction, WorkflowTrigger

logger = logging.getLogger(__name__)


class WorkflowQuerySet(StandardQuerySet["Workflow"]):
    """
    Specialized queryset for interacting with Paperless-NGX workflows.

    Extends StandardQuerySet to provide workflow-specific filtering methods,
    making it easier to query workflows by attributes such as name, order,
    and enabled status. The queryset is lazy-loaded, meaning API requests
    are only made when data is actually needed.

    Examples:
        Get all enabled workflows:
            >>> enabled_workflows = client.workflows.filter(enabled=True)
            >>> # Or using the specialized method
            >>> enabled_workflows = client.workflows.enabled()

        Filter workflows by name:
            >>> tax_workflows = client.workflows.name("tax")

    """

    def name(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter workflows by name.

        Args:
            value: The workflow name to filter by.
            exact: If True, match the exact name; if False, use contains matching.
            case_insensitive: If True, ignore case when matching.

        Returns:
            A filtered WorkflowQuerySet containing matching workflows.

        Examples:
            Find workflows with exact name:
                >>> invoice_workflows = client.workflows.name("Invoice Processing")

            Find workflows containing a string (case-insensitive):
                >>> invoice_workflows = client.workflows.name("invoice", exact=False)

        """
        return self.filter_field_by_str("name", value, exact=exact, case_insensitive=case_insensitive)

    def order(self, value: int) -> Self:
        """
        Filter workflows by their execution order.

        Paperless-NGX workflows have an order value that determines their
        execution sequence. This method finds workflows with a specific order value.

        Args:
            value: The order value to filter by.

        Returns:
            A filtered WorkflowQuerySet containing workflows with the specified order.

        """
        return self.filter(order=value)

    def enabled(self, value: bool = True) -> Self:
        """
        Filter workflows by their enabled status.

        Args:
            value: If True, return only enabled workflows; if False, return only disabled workflows.

        Returns:
            A filtered WorkflowQuerySet containing workflows with the specified enabled status.

        Examples:
            Get all enabled workflows:
                >>> active_workflows = client.workflows.enabled()

            Get all disabled workflows:
                >>> inactive_workflows = client.workflows.enabled(False)

        """
        return self.filter(enabled=value)


class WorkflowActionQuerySet(StandardQuerySet["WorkflowAction"]):
    """
    Specialized queryset for interacting with Paperless-NGX workflow actions.

    Extends StandardQuerySet to provide workflow action-specific filtering methods,
    making it easier to query actions by attributes such as type and assigned metadata.
    Workflow actions define what happens when a workflow is triggered, such as
    assigning tags, correspondents, or document types to documents.

    Examples:
        Get actions that assign a specific tag:
            >>> tag_actions = client.workflow_actions.assign_tags(5)

        Find actions that set a specific title:
            >>> title_actions = client.workflow_actions.assign_title("Invoice")

    """

    def type(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter workflow actions by their type.

        Workflow actions in Paperless-NGX have different types that determine
        what they do (e.g., assign metadata, move document, etc.).

        Args:
            value: The action type to filter by.
            exact: If True, match the exact type; if False, use contains matching.
            case_insensitive: If True, ignore case when matching.

        Returns:
            A filtered WorkflowActionQuerySet containing actions of the specified type.

        Examples:
            Find all actions that assign metadata:
                >>> assign_actions = client.workflow_actions.type("assign")

        """
        return self.filter_field_by_str("type", value, exact=exact, case_insensitive=case_insensitive)

    def assign_title(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter workflow actions by the title they assign to documents.

        Find workflow actions that set a specific document title when triggered.

        Args:
            value: The title text to filter by.
            exact: If True, match the exact title; if False, use contains matching.
            case_insensitive: If True, ignore case when matching.

        Returns:
            A filtered WorkflowActionQuerySet containing actions that assign the specified title.

        Examples:
            Find actions that set titles containing "Invoice":
                >>> invoice_actions = client.workflow_actions.assign_title("Invoice", exact=False)

        """
        return self.filter_field_by_str("assign_title", value, exact=exact, case_insensitive=case_insensitive)

    def assign_tags(self, value: int | list[int]) -> Self:
        """
        Filter workflow actions by the tags they assign to documents.

        Find workflow actions that assign specific tags to documents when triggered.
        Can filter by a single tag ID or multiple tag IDs.

        Args:
            value: The tag ID or list of tag IDs to filter by.

        Returns:
            A filtered WorkflowActionQuerySet containing actions that assign the specified tags.

        Examples:
            Find actions that assign a specific tag:
                >>> tax_tag_actions = client.workflow_actions.assign_tags(5)

            Find actions that assign any of several tags:
                >>> financial_tag_actions = client.workflow_actions.assign_tags([5, 8, 12])

        """
        if isinstance(value, int):
            return self.filter(assign_tags__contains=value)
        return self.filter(assign_tags__overlap=value)

    def assign_correspondent(self, value: int) -> Self:
        """
        Filter workflow actions by the correspondent they assign to documents.

        Find workflow actions that assign a specific correspondent to documents when triggered.

        Args:
            value: The correspondent ID to filter by.

        Returns:
            A filtered WorkflowActionQuerySet containing actions that assign the specified correspondent.

        Examples:
            Find actions that assign a specific correspondent:
                >>> vendor_actions = client.workflow_actions.assign_correspondent(3)

        """
        return self.filter(assign_correspondent=value)

    def assign_document_type(self, value: int) -> Self:
        """
        Filter workflow actions by the document type they assign.

        Find workflow actions that assign a specific document type to documents when triggered.

        Args:
            value: The document type ID to filter by.

        Returns:
            A filtered WorkflowActionQuerySet containing actions that assign the specified document type.

        Examples:
            Find actions that assign a specific document type:
                >>> invoice_type_actions = client.workflow_actions.assign_document_type(2)

        """
        return self.filter(assign_document_type=value)

    def assign_storage_path(self, value: int) -> Self:
        """
        Filter workflow actions by the storage path they assign to documents.

        Find workflow actions that assign a specific storage path to documents when triggered.

        Args:
            value: The storage path ID to filter by.

        Returns:
            A filtered WorkflowActionQuerySet containing actions that assign the specified storage path.

        Examples:
            Find actions that assign a specific storage path:
                >>> tax_path_actions = client.workflow_actions.assign_storage_path(4)

        """
        return self.filter(assign_storage_path=value)

    def assign_owner(self, value: int) -> Self:
        """
        Filter workflow actions by the owner they assign to documents.

        Find workflow actions that assign a specific owner (user) to documents when triggered.

        Args:
            value: The owner (user) ID to filter by.

        Returns:
            A filtered WorkflowActionQuerySet containing actions that assign the specified owner.

        Examples:
            Find actions that assign documents to a specific user:
                >>> admin_actions = client.workflow_actions.assign_owner(1)

        """
        return self.filter(assign_owner=value)


class WorkflowTriggerQuerySet(StandardQuerySet["WorkflowTrigger"]):
    """
    Specialized queryset for interacting with Paperless-NGX workflow triggers.

    Extends StandardQuerySet to provide workflow trigger-specific filtering methods,
    making it easier to query triggers by attributes such as type and filter conditions.
    Workflow triggers define when a workflow should be executed, such as when a document
    is added with specific attributes or matches certain criteria.

    Examples:
        Get all triggers of a specific type:
            >>> consumption_triggers = client.workflow_triggers.type(1)  # Type 1 might be "document added"

        Find triggers that look for specific tags:
            >>> tax_triggers = client.workflow_triggers.has_tags(5)  # Tag ID 5 might be "Tax"

    """

    def type(self, value: int) -> Self:
        """
        Filter workflow triggers by their type.

        Workflow triggers in Paperless-NGX have different types that determine
        when they activate (e.g., document added, document consumed, etc.).

        Args:
            value: The trigger type ID to filter by.

        Returns:
            A filtered WorkflowTriggerQuerySet containing triggers of the specified type.

        Examples:
            Find all triggers that activate when documents are consumed:
                >>> consumption_triggers = client.workflow_triggers.type(1)  # Assuming 1 is consumption type

        """
        return self.filter(type=value)

    def filter_path(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter workflow triggers by their path filter condition.

        Find workflow triggers that activate based on a document's source path
        matching specific criteria.

        Args:
            value: The path filter text to match.
            exact: If True, match the exact path; if False, use contains matching.
            case_insensitive: If True, ignore case when matching.

        Returns:
            A filtered WorkflowTriggerQuerySet containing triggers with the specified path filter.

        Examples:
            Find triggers that look for documents from a specific directory:
                >>> inbox_triggers = client.workflow_triggers.filter_path("/inbox/")

            Find triggers that look for documents from any path containing a string:
                >>> invoice_triggers = client.workflow_triggers.filter_path("invoices", exact=False)

        """
        return self.filter_field_by_str("filter_path", value, exact=exact, case_insensitive=case_insensitive)

    def filter_filename(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter workflow triggers by their filename filter condition.

        Find workflow triggers that activate based on a document's original
        filename matching specific criteria.

        Args:
            value: The filename filter text to match.
            exact: If True, match the exact filename; if False, use contains matching.
            case_insensitive: If True, ignore case when matching.

        Returns:
            A filtered WorkflowTriggerQuerySet containing triggers with the specified filename filter.

        Examples:
            Find triggers that look for documents with specific text in filenames:
                >>> invoice_triggers = client.workflow_triggers.filter_filename("invoice", exact=False)

            Find triggers that look for specific file types:
                >>> pdf_triggers = client.workflow_triggers.filter_filename(".pdf", exact=False)

        """
        return self.filter_field_by_str("filter_filename", value, exact=exact, case_insensitive=case_insensitive)

    def filter_mailrule(self, value: str, *, exact: bool = True, case_insensitive: bool = True) -> Self:
        """
        Filter workflow triggers by their mail rule filter condition.

        Find workflow triggers that activate based on a document's associated
        mail rule matching specific criteria.

        Args:
            value: The mail rule filter text to match.
            exact: If True, match the exact mail rule; if False, use contains matching.
            case_insensitive: If True, ignore case when matching.

        Returns:
            A filtered WorkflowTriggerQuerySet containing triggers with the specified mail rule filter.

        Examples:
            Find triggers that look for documents from a specific mail rule:
                >>> vendor_mail_triggers = client.workflow_triggers.filter_mailrule("vendor@example.com")

            Find triggers that look for documents from mail rules containing specific text:
                >>> invoice_mail_triggers = client.workflow_triggers.filter_mailrule("invoice", exact=False)

        """
        return self.filter_field_by_str("filter_mailrule", value, exact=exact, case_insensitive=case_insensitive)

    def has_tags(self, value: int | list[int]) -> Self:
        """
        Filter workflow triggers by their tag filter condition.

        Find workflow triggers that activate based on a document having specific tags.
        Can filter by a single tag ID or multiple tag IDs.

        Args:
            value: The tag ID or list of tag IDs to filter by.

        Returns:
            A filtered WorkflowTriggerQuerySet containing triggers with the specified tag filter.

        Examples:
            Find triggers that look for documents with a specific tag:
                >>> tax_triggers = client.workflow_triggers.has_tags(5)

            Find triggers that look for documents with any of several tags:
                >>> financial_triggers = client.workflow_triggers.has_tags([5, 8, 12])

        """
        if isinstance(value, int):
            return self.filter(filter_has_tags__contains=value)
        return self.filter(filter_has_tags__overlap=value)

    def has_correspondent(self, value: int) -> Self:
        """
        Filter workflow triggers by their correspondent filter condition.

        Find workflow triggers that activate based on a document having a specific correspondent.

        Args:
            value: The correspondent ID to filter by.

        Returns:
            A filtered WorkflowTriggerQuerySet containing triggers with the specified correspondent filter.

        Examples:
            Find triggers that look for documents from a specific correspondent:
                >>> vendor_triggers = client.workflow_triggers.has_correspondent(3)

        """
        return self.filter(filter_has_correspondent=value)

    def has_document_type(self, value: int) -> Self:
        """
        Filter workflow triggers by their document type filter condition.

        Find workflow triggers that activate based on a document having a specific document type.

        Args:
            value: The document type ID to filter by.

        Returns:
            A filtered WorkflowTriggerQuerySet containing triggers with the specified document type filter.

        Examples:
            Find triggers that look for documents of a specific type:
                >>> invoice_triggers = client.workflow_triggers.has_document_type(2)

        """
        return self.filter(filter_has_document_type=value)
