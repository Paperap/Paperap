"""



 ----------------------------------------------------------------------------

    METADATA:

        File:    __init__.py
        Project: paperap
        Created: 2025-03-04
        Version: 0.0.5
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-04     By Jess Mann

"""
from paperap.tests.utils import load_sample_data, defaults, random_string, random_json
from paperap.tests.testcase import TestMixin
from paperap.tests.unittest import (CorrespondentUnitTest, CustomFieldUnitTest, DocumentUnitTest,
                                    DocumentTypeUnitTest, GroupUnitTest, ProfileUnitTest,
                                    SavedViewUnitTest, ShareLinksUnitTest,
                                    StoragePathUnitTest, TagUnitTest, TaskUnitTest,
                                    UnitTestCase, UISettingsUnitTest, UserUnitTest,
                                    WorkflowActionUnitTest, WorkflowUnitTest,
                                    WorkflowTriggerUnitTest)
from paperap.tests.pytest import (CorrespondentPyTest, CustomFieldPyTest, DocumentPyTest,
                                    DocumentTypePyTest, GroupPyTest, ProfilePyTest,
                                    SavedViewPyTest, ShareLinksPyTest,
                                    StoragePathPyTest, TagPyTest, TaskPyTest,
                                    PyTestCase, UISettingsPyTest, UserPyTest,
                                    WorkflowActionPyTest, WorkflowPyTest,
                                    WorkflowTriggerPyTest)
