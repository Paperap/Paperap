#!/usr/bin/env python3
"""
Find test leaks by running each test class individually and then the full test suite.
This helps identify which tests are not cleaning up properly and affecting other tests.
"""

import importlib
import inspect
import sys
import unittest
from pathlib import Path

# Import the test module to examine
from tests.unit.test_client import *


def find_test_classes():
    """Find all test classes in the imported module."""
    test_classes = []
    for name, obj in inspect.getmembers(sys.modules["tests.unit.test_client"]):
        if inspect.isclass(obj) and issubclass(obj, unittest.TestCase) and obj != unittest.TestCase:
            test_classes.append(obj)
    return test_classes


def run_test_class(test_class):
    """Run a single test class."""
    suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_full_test_module():
    """Run the entire test module."""
    # Reload the module to ensure a clean state
    importlib.reload(sys.modules["tests.unit.test_client"])

    # Run all tests in the module
    suite = unittest.TestLoader().loadTestsFromName("tests.unit.test_client")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def main():
    print("Finding test classes in tests.unit.test_client...")
    test_classes = find_test_classes()
    print(f"Found {len(test_classes)} test classes.")

    problematic_classes = []

    for test_class in test_classes:
        class_name = test_class.__name__
        print(f"\n{'=' * 80}")
        print(f"Testing class: {class_name}")
        print(f"{'=' * 80}")

        # Run just this test class
        print(f"Running {class_name} in isolation...")
        class_success = run_test_class(test_class)
        print(f"Result: {'SUCCESS' if class_success else 'FAILURE'}")

        # Now run the full test module to see if this test affected others
        print(f"\nRunning full test module after {class_name}...")
        module_success = run_full_test_module()
        print(f"Result: {'SUCCESS' if module_success else 'FAILURE'}")

        if class_success and not module_success:
            print(f"\n⚠️ WARNING: {class_name} passes in isolation but causes failures when run before other tests.")
            problematic_classes.append(class_name)

    print("\n\n=== SUMMARY ===")
    if problematic_classes:
        print("The following test classes may not be cleaning up properly:")
        for name in problematic_classes:
            print(f" - {name}")
        print("\nThese tests likely leave global state that affects later tests.")
    else:
        print("No problematic test classes identified.")
        print("The issue might be more complex or related to the test runner's order.")


if __name__ == "__main__":
    main()
