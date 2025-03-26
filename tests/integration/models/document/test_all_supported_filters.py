#!/usr/bin/env python3
"""
Integration tests covering all supported document filtering parameters in a DRY manner.
"""

import datetime
import unittest

from paperap.client import PaperlessClient


class TestAllSupportedDocumentFilters(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        client = PaperlessClient()
        cls.client = client
        cls.all_documents = list(client.documents().all())

    def _assert_filter_result(self, filter_key: str, filter_value, predicate: callable) -> None:
        filtered = list(self.client.documents().filter(**{filter_key: filter_value}))
        expected = [doc for doc in self.all_documents if predicate(doc)]
        self.assertEqual(len(filtered), len(expected), f"Filter {filter_key} with value {filter_value} failed")

    def test_all_supported_filters(self) -> None:
        if not self.all_documents:
            self.skipTest("No documents available for testing")
        test_cases = []
        doc0 = self.all_documents[0]

        # id filters
        test_cases.append(("id", doc0.id, lambda d: d.id == doc0.id))
        if len(self.all_documents) >= 2:
            ids = [d.id for d in self.all_documents[:2]]
            test_cases.append(("id__in", ids, lambda d: d.id in ids))

        # title filters
        if hasattr(doc0, "title") and doc0.title:
            prefix = doc0.title[:3].lower()
            test_cases.append(("title__istartswith", prefix, lambda d: hasattr(d, "title") and d.title and d.title.lower().startswith(prefix)))
            test_cases.append(("title__icontains", doc0.title.lower(), lambda d: hasattr(d, "title") and d.title and doc0.title.lower() in d.title.lower()))
            test_cases.append(("title__iexact", doc0.title.lower(), lambda d: hasattr(d, "title") and d.title and d.title.lower() == doc0.title.lower()))
            suffix = doc0.title[-3:].lower()
            test_cases.append(("title__iendswith", suffix, lambda d: hasattr(d, "title") and d.title and d.title.lower().endswith(suffix)))

        # content filters
        if hasattr(doc0, "content") and doc0.content:
            prefix = doc0.content[:3].lower()
            test_cases.append(("content__istartswith", prefix, lambda d: hasattr(d, "content") and d.content and d.content.lower().startswith(prefix)))
            test_cases.append(("content__icontains", doc0.content.lower(), lambda d: hasattr(d, "content") and d.content and doc0.content.lower() in d.content.lower()))
            test_cases.append(("content__iexact", doc0.content.lower(), lambda d: hasattr(d, "content") and d.content and d.content.lower() == doc0.content.lower()))
            suffix = doc0.content[-3:].lower()
            test_cases.append(("content__iendswith", suffix, lambda d: hasattr(d, "content") and d.content and d.content.lower().endswith(suffix)))
            frag = doc0.content[1:4] if len(doc0.content) >= 4 else doc0.content
            test_cases.append(("content__contains", frag, lambda d: hasattr(d, "content") and d.content and frag in d.content))
        # archive_serial_number filters
        if hasattr(doc0, "archive_serial_number") and doc0.archive_serial_number is not None:
            asn = doc0.archive_serial_number
            test_cases.append(("archive_serial_number", asn, lambda d: hasattr(d, "archive_serial_number") and d.archive_serial_number == asn))

        docs_asn = [d for d in self.all_documents if hasattr(d, "archive_serial_number") and d.archive_serial_number is not None]
        if docs_asn:
            docs_asn.sort(key=lambda d: d.archive_serial_number)
            mid = docs_asn[len(docs_asn) // 2].archive_serial_number
            test_cases.append(("archive_serial_number__gt", mid, lambda d: hasattr(d, "archive_serial_number") and d.archive_serial_number > mid))
            test_cases.append(("archive_serial_number__gte", mid, lambda d: hasattr(d, "archive_serial_number") and d.archive_serial_number >= mid))
            test_cases.append(("archive_serial_number__lt", mid, lambda d: hasattr(d, "archive_serial_number") and d.archive_serial_number < mid))
            test_cases.append(("archive_serial_number__lte", mid, lambda d: hasattr(d, "archive_serial_number") and d.archive_serial_number <= mid))
            test_cases.append(("archive_serial_number__isnull", False, lambda d: hasattr(d, "archive_serial_number") and d.archive_serial_number is not None))
            test_cases.append(("archive_serial_number__isnull", True, lambda d: not (hasattr(d, "archive_serial_number") and d.archive_serial_number is not None)))

        # correspondent filters
        if hasattr(doc0, "correspondent"):
            if doc0.correspondent and hasattr(doc0.correspondent, "id"):
                cid = doc0.correspondent.id
                test_cases.append(("correspondent__id", cid, lambda d: hasattr(d, "correspondent") and d.correspondent and d.correspondent.id == cid))
                test_cases.append(("correspondent__isnull", False, lambda d: hasattr(d, "correspondent") and d.correspondent))
            else:
                test_cases.append(("correspondent__isnull", True, lambda d: not (hasattr(d, "correspondent") and d.correspondent)))

        # created date filter
        if hasattr(doc0, "created") and doc0.created:
            dt = doc0.created
            test_cases.append(("created__year", dt.year, lambda d: hasattr(d, "created") and d.created.year == dt.year))

        # added date filter
        if hasattr(doc0, "added") and doc0.added:
            dt = doc0.added
            test_cases.append(("added__year", dt.year, lambda d: hasattr(d, "added") and d.added.year == dt.year))

        # original_filename filter
        if hasattr(doc0, "original_filename") and doc0.original_filename:
            test_cases.append(("original_filename__iexact", doc0.original_filename.lower(), lambda d: hasattr(d, "original_filename") and d.original_filename.lower() == doc0.original_filename.lower()))

        # checksum filter
        if hasattr(doc0, "checksum") and doc0.checksum:
            test_cases.append(("checksum__iexact", doc0.checksum.lower(), lambda d: hasattr(d, "checksum") and d.checksum.lower() == doc0.checksum.lower()))

        # tag filters
        if hasattr(doc0, "tag_ids") and doc0.tag_ids:
            t = doc0.tag_ids[0]
            test_cases.append(("tags__id", t, lambda d: hasattr(d, "tag_ids") and t in d.tag_ids))

        # document_type filters
        if hasattr(doc0, "document_type") and doc0.document_type:
            if hasattr(doc0.document_type, "id"):
                dtid = doc0.document_type.id
                test_cases.append(("document_type__id", dtid, lambda d: hasattr(d, "document_type") and getattr(d.document_type, "id", None) == dtid))
            if hasattr(doc0.document_type, "name") and doc0.document_type.name:
                n = doc0.document_type.name.lower()
                test_cases.append(("document_type__iexact", n, lambda d: hasattr(d, "document_type") and d.document_type and d.document_type.name.lower() == n))

        # storage_path filters
        if hasattr(doc0, "storage_path") and doc0.storage_path:
            if hasattr(doc0.storage_path, "id"):
                spid = doc0.storage_path.id
                test_cases.append(("storage_path__id", spid, lambda d: hasattr(d, "storage_path") and getattr(d.storage_path, "id", None) == spid))
            if hasattr(doc0.storage_path, "name") and doc0.storage_path.name:
                sname = doc0.storage_path.name.lower()
                test_cases.append(("storage_path__iexact", sname, lambda d: hasattr(d, "storage_path") and d.storage_path and d.storage_path.name.lower() == sname))

        # owner filters
        if hasattr(doc0, "owner") and doc0.owner:
            if hasattr(doc0.owner, "id"):
                oid = doc0.owner.id
                test_cases.append(("owner__id", oid, lambda d: hasattr(d, "owner") and getattr(d.owner, "id", None) == oid))

        # special filters (placeholders as actual logic may reside on the server)
        test_cases.append(("is_in_inbox", True, lambda d: True))
        test_cases.append(("title_content", "", lambda d: True))

        # custom fields filter
        if hasattr(doc0, "custom_fields") and doc0.custom_fields:
            cf_val = str(doc0.custom_fields[0])
            test_cases.append(("custom_fields__icontains", cf_val.lower(), lambda d: hasattr(d, "custom_fields") and cf_val.lower() in str(d.custom_fields).lower()))
    
        for key, value, predicate in test_cases:
            with self.subTest(filter=key):
                self._assert_filter_result(key, value, predicate)
    
    
if __name__ == "__main__":
    unittest.main()
