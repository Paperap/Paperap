"""



 ----------------------------------------------------------------------------

    METADATA:

        File:    __init__.py
        Project: paperap
        Created: 2025-03-04
        Version: 0.0.8
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-04     By Jess Mann

"""
from tests.lib.utils import load_sample_data, defaults, create_client, create_resource
from tests.lib.testcase import TestMixin
from tests.lib.unittest import (CorrespondentUnitTest, CustomFieldUnitTest, DocumentUnitTest,
                                    DocumentTypeUnitTest, GroupUnitTest, ProfileUnitTest,
                                    SavedViewUnitTest, ShareLinksUnitTest,
                                    StoragePathUnitTest, TagUnitTest, TaskUnitTest,
                                    UnitTestCase, UISettingsUnitTest, UserUnitTest,
                                    WorkflowActionUnitTest, WorkflowUnitTest,
                                    WorkflowTriggerUnitTest, TestConfigurationError)
from tests.lib.pytest import (CorrespondentPyTest, CustomFieldPyTest, DocumentPyTest,
                                    DocumentTypePyTest, GroupPyTest, ProfilePyTest,
                                    SavedViewPyTest, ShareLinksPyTest,
                                    StoragePathPyTest, TagPyTest, TaskPyTest,
                                    PyTestCase, UISettingsPyTest, UserPyTest,
                                    WorkflowActionPyTest, WorkflowPyTest,
                                    WorkflowTriggerPyTest)
