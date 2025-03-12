"""




 ----------------------------------------------------------------------------

    METADATA:

        File:    test_custom_field.py
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
import os
from typing import Iterable, override
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from pydantic import ValidationError
from paperap.tests import UnitTestCase, load_sample_data, CorrespondentUnitTest