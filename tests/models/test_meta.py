"""



 ----------------------------------------------------------------------------

    METADATA:

        File:    test_meta.py
        Project: paperap
        Created: 2025-03-09
        Version: 0.0.5
        Author:  Jess Mann
        Email:   jess@jmann.me
        Copyright (c) 2025 Jess Mann

 ----------------------------------------------------------------------------

    LAST MODIFIED:

        2025-03-09     By Jess Mann

"""
from typing import Any, ClassVar, override
import unittest
from paperap.models.abstract import StandardModel
from paperap.resources.base import StandardResource
from paperap.tests import UnitTestCase

class SampleResource(StandardResource):
    """
    Sample resource for testing purposes.
    """
    name = "sample"
    model_class = StandardModel

class TestStandardModelMeta(UnitTestCase):
    @override
    def setUp(self):
        super().setUp()
        self.resource = SampleResource(self.client)

    def test_subclass_meta_inheritance(self):
        """Ensure that subclasses inherit Meta correctly without modifying parents."""

        class ParentModel(StandardModel):
            field1: str = "parent-field1"

            class Meta(StandardModel.Meta):
                resource = self.resource
                read_only_fields: ClassVar[set[str]] = {"parent_field"}
                supported_filtering_params: ClassVar[set[str]] = {"parent_filter"}
                foo = "parent-foo"
                bar = "parent-bar"

            @classmethod
            def __init_subclass__(cls, **kwargs : Any) -> None:
                super().__init_subclass__(**kwargs)
                cls.Meta.foo = "parent-subclass-foo-update"

        class ChildModel(ParentModel):
            field1: str = "child-field1"
            field2: str = "child-field2"

            class Meta(ParentModel.Meta):
                resource = self.resource
                read_only_fields: ClassVar[set[str]] = {"child_field"}
                supported_filtering_params: ClassVar[set[str]] = {"child_filter"}
                foo = "child-foo"
                bar = "child-bar"

            @classmethod
            def __init_subclass__(cls, **kwargs : Any) -> None:
                super().__init_subclass__(**kwargs)
                cls.Meta.foo = "child-subclass-foo-update"

        class SubChildModel(ChildModel):
            field1: str = "sub-child-field1"
            field2: str = "sub-child-field2"
            field3: str = "sub-child-field3"

            class Meta(ChildModel.Meta):
                read_only_fields: ClassVar[set[str]] = {"sub_child_field"}
                supported_filtering_params: ClassVar[set[str]] = {"sub_child_filter"}
                foo = "subchild-foo"
                bar = "subchild-bar"

            @classmethod
            def __init_subclass__(cls, **kwargs : Any) -> None:
                super().__init_subclass__(**kwargs)
                cls.Meta.foo = "subchild-subclass-foo-update"

        # Test parent
        self.assertEqual(ParentModel.Meta.foo, "parent-foo")
        self.assertEqual(ParentModel.Meta.bar, "parent-bar")
        self.assertIn("parent_field", ParentModel.Meta.read_only_fields)
        self.assertIn("parent_filter", ParentModel.Meta.supported_filtering_params)
        self.assertNotIn("child_field", ParentModel.Meta.read_only_fields)
        self.assertNotIn("child_filter", ParentModel.Meta.supported_filtering_params)
        self.assertNotIn("sub_child_field", ParentModel.Meta.read_only_fields)
        self.assertNotIn("sub_child_filter", ParentModel.Meta.supported_filtering_params)

        # Test child
        self.assertEqual(ChildModel.Meta.foo, "parent-subclass-foo-update")
        self.assertEqual(ChildModel.Meta.bar, "child-bar")
        self.assertIn("parent_field", ChildModel.Meta.read_only_fields)
        self.assertIn("parent_filter", ChildModel.Meta.supported_filtering_params)
        self.assertIn("child_field", ChildModel.Meta.read_only_fields)
        self.assertIn("child_filter", ChildModel.Meta.supported_filtering_params)
        self.assertNotIn("sub_child_field", ChildModel.Meta.read_only_fields)
        self.assertNotIn("sub_child_filter", ChildModel.Meta.supported_filtering_params)

        # Test subchild
        self.assertEqual(SubChildModel.Meta.foo, "child-subclass-foo-update")
        self.assertEqual(SubChildModel.Meta.bar, "subchild-bar")
        self.assertIn("parent_field", SubChildModel.Meta.read_only_fields)
        self.assertIn("parent_filter", SubChildModel.Meta.supported_filtering_params)
        self.assertIn("child_field", SubChildModel.Meta.read_only_fields)
        self.assertIn("child_filter", SubChildModel.Meta.supported_filtering_params)
        self.assertIn("sub_child_field", SubChildModel.Meta.read_only_fields)
        self.assertIn("sub_child_filter", SubChildModel.Meta.supported_filtering_params)

        # Instantiate models
        parent = ParentModel()
        child = ChildModel()
        subchild = SubChildModel()

        self.assertIsInstance(parent.Meta, type(StandardModel.Meta))
        self.assertIsInstance(parent._meta, StandardModel.Meta) # type: ignore
        self.assertEqual(parent.Meta.foo, "parent-foo")
        self.assertEqual(parent._meta.foo, "parent-foo") # type: ignore
        self.assertEqual(parent.Meta.bar, "parent-bar")
        self.assertEqual(parent._meta.bar, "parent-bar") # type: ignore
        self.assertEqual(parent.field1, "parent-field1")
        self.assertIn("parent_field", parent.Meta.read_only_fields)
        self.assertIn("parent_filter", parent.Meta.supported_filtering_params)
        self.assertNotIn("child_field", parent.Meta.read_only_fields)
        self.assertNotIn("child_filter", parent.Meta.supported_filtering_params)
        self.assertNotIn("sub_child_field", parent.Meta.read_only_fields)
        self.assertNotIn("sub_child_filter", parent.Meta.supported_filtering_params)
        self.assertIn("parent_field", parent._meta.read_only_fields) # type: ignore
        self.assertIn("parent_filter", parent._meta.supported_filtering_params) # type: ignore
        self.assertNotIn("child_field", parent._meta.read_only_fields) # type: ignore
        self.assertNotIn("child_filter", parent._meta.supported_filtering_params) # type: ignore
        self.assertNotIn("sub_child_field", parent._meta.read_only_fields) # type: ignore
        self.assertNotIn("sub_child_filter", parent._meta.supported_filtering_params) # type: ignore

        self.assertIsInstance(child.Meta, type(StandardModel.Meta))
        self.assertIsInstance(child._meta, StandardModel.Meta) # type: ignore
        self.assertEqual(child.Meta.foo, "parent-subclass-foo-update")
        self.assertEqual(child._meta.foo, "parent-subclass-foo-update") # type: ignore
        self.assertEqual(child.Meta.bar, "child-bar")
        self.assertEqual(child._meta.bar, "child-bar") # type: ignore
        self.assertEqual(child.field1, "child-field1")
        self.assertEqual(child.field2, "child-field2")
        self.assertIn("parent_field", child.Meta.read_only_fields)
        self.assertIn("parent_filter", child.Meta.supported_filtering_params)
        self.assertIn("child_field", child.Meta.read_only_fields)
        self.assertIn("child_filter", child.Meta.supported_filtering_params)
        self.assertNotIn("sub_child_field", child.Meta.read_only_fields)
        self.assertNotIn("sub_child_filter", child.Meta.supported_filtering_params)
        self.assertIn("parent_field", child._meta.read_only_fields) # type: ignore
        self.assertIn("parent_filter", child._meta.supported_filtering_params) # type: ignore
        self.assertIn("child_field", child._meta.read_only_fields) # type: ignore
        self.assertIn("child_filter", child._meta.supported_filtering_params) # type: ignore
        self.assertNotIn("sub_child_field", child._meta.read_only_fields) # type: ignore
        self.assertNotIn("sub_child_filter", child._meta.supported_filtering_params) # type: ignore

        self.assertIsInstance(subchild.Meta, type(StandardModel.Meta))
        self.assertIsInstance(subchild._meta, StandardModel.Meta) # type: ignore
        self.assertEqual(subchild.Meta.foo, "child-subclass-foo-update")
        self.assertEqual(subchild._meta.foo, "child-subclass-foo-update") # type: ignore
        self.assertEqual(subchild.Meta.bar, "subchild-bar")
        self.assertEqual(subchild._meta.bar, "subchild-bar") # type: ignore
        self.assertEqual(subchild.field1, "sub-child-field1")
        self.assertEqual(subchild.field2, "sub-child-field2")
        self.assertEqual(subchild.field3, "sub-child-field3")
        self.assertIn("parent_field", subchild.Meta.read_only_fields)
        self.assertIn("parent_filter", subchild.Meta.supported_filtering_params)
        self.assertIn("child_field", subchild.Meta.read_only_fields)
        self.assertIn("child_filter", subchild.Meta.supported_filtering_params)
        self.assertIn("sub_child_field", subchild.Meta.read_only_fields)
        self.assertIn("sub_child_filter", subchild.Meta.supported_filtering_params)
        self.assertIn("parent_field", subchild._meta.read_only_fields) # type: ignore
        self.assertIn("parent_filter", subchild._meta.supported_filtering_params) # type: ignore
        self.assertIn("child_field", subchild._meta.read_only_fields) # type: ignore
        self.assertIn("child_filter", subchild._meta.supported_filtering_params) # type: ignore
        self.assertIn("sub_child_field", subchild._meta.read_only_fields) # type: ignore
        self.assertIn("sub_child_filter", subchild._meta.supported_filtering_params) # type: ignore

    def test_subclass_meta_missing(self):
        """
        Ensure that subclasses inherit Meta correctly even when a Meta class is not defined.

        Identical to the test above, except that ChildModel does not define a Meta class.
        """

        class ParentModel(StandardModel):
            field1: str = "parent-field1"

            class Meta(StandardModel.Meta):
                resource = self.resource
                read_only_fields: ClassVar[set[str]] = {"parent_field"}
                supported_filtering_params: ClassVar[set[str]] = {"parent_filter"}
                foo = "parent-foo"
                bar = "parent-bar"

            @classmethod
            def __init_subclass__(cls, **kwargs : Any) -> None:
                super().__init_subclass__(**kwargs)
                cls.Meta.foo = "parent-subclass-foo-update"

        class ChildModel(ParentModel):
            field1: str = "child-field1"
            field2: str = "child-field2"

            @classmethod
            def __init_subclass__(cls, **kwargs : Any) -> None:
                super().__init_subclass__(**kwargs)
                cls.Meta.foo = "child-subclass-foo-update"

        class SubChildModel(ChildModel):
            field1: str = "sub-child-field1"
            field2: str = "sub-child-field2"
            field3: str = "sub-child-field3"

            class Meta(ChildModel.Meta):
                read_only_fields: ClassVar[set[str]] = {"sub_child_field"}
                supported_filtering_params: ClassVar[set[str]] = {"sub_child_filter"}
                foo = "subchild-foo"
                bar = "subchild-bar"

            @classmethod
            def __init_subclass__(cls, **kwargs : Any) -> None:
                super().__init_subclass__(**kwargs)
                cls.Meta.foo = "subchild-subclass-foo-update"

        # Test parent
        self.assertEqual(ParentModel.Meta.foo, "parent-foo")
        self.assertEqual(ParentModel.Meta.bar, "parent-bar")
        self.assertIn("parent_field", ParentModel.Meta.read_only_fields)
        self.assertIn("parent_filter", ParentModel.Meta.supported_filtering_params)
        self.assertNotIn("child_field", ParentModel.Meta.read_only_fields)
        self.assertNotIn("child_filter", ParentModel.Meta.supported_filtering_params)
        self.assertNotIn("sub_child_field", ParentModel.Meta.read_only_fields)
        self.assertNotIn("sub_child_filter", ParentModel.Meta.supported_filtering_params)

        # Test child
        self.assertEqual(ChildModel.Meta.foo, "parent-subclass-foo-update")
        self.assertEqual(ChildModel.Meta.bar, "parent-bar")
        self.assertIn("parent_field", ChildModel.Meta.read_only_fields)
        self.assertIn("parent_filter", ChildModel.Meta.supported_filtering_params)
        self.assertNotIn("sub_child_field", ChildModel.Meta.read_only_fields)
        self.assertNotIn("sub_child_filter", ChildModel.Meta.supported_filtering_params)

        # Test subchild
        self.assertEqual(SubChildModel.Meta.foo, "child-subclass-foo-update")
        self.assertEqual(SubChildModel.Meta.bar, "subchild-bar")
        self.assertIn("parent_field", SubChildModel.Meta.read_only_fields)
        self.assertIn("parent_filter", SubChildModel.Meta.supported_filtering_params)
        self.assertIn("sub_child_field", SubChildModel.Meta.read_only_fields)
        self.assertIn("sub_child_filter", SubChildModel.Meta.supported_filtering_params)

        # Instantiate models
        parent = ParentModel()
        child = ChildModel()
        subchild = SubChildModel()

        self.assertIsInstance(parent.Meta, type(StandardModel.Meta))
        self.assertIsInstance(parent._meta, StandardModel.Meta) # type: ignore
        self.assertEqual(parent.Meta.foo, "parent-foo")
        self.assertEqual(parent._meta.foo, "parent-foo") # type: ignore
        self.assertEqual(parent.Meta.bar, "parent-bar")
        self.assertEqual(parent._meta.bar, "parent-bar") # type: ignore
        self.assertEqual(parent.field1, "parent-field1")
        self.assertIn("parent_field", parent.Meta.read_only_fields)
        self.assertIn("parent_filter", parent.Meta.supported_filtering_params)
        self.assertNotIn("sub_child_field", parent.Meta.read_only_fields)
        self.assertNotIn("sub_child_filter", parent.Meta.supported_filtering_params)
        self.assertIn("parent_field", parent._meta.read_only_fields) # type: ignore
        self.assertIn("parent_filter", parent._meta.supported_filtering_params) # type: ignore
        self.assertNotIn("sub_child_field", parent._meta.read_only_fields) # type: ignore
        self.assertNotIn("sub_child_filter", parent._meta.supported_filtering_params) # type: ignore

        self.assertIsInstance(child.Meta, type(StandardModel.Meta))
        self.assertIsInstance(child._meta, StandardModel.Meta) # type: ignore
        self.assertEqual(child.Meta.foo, "parent-subclass-foo-update")
        self.assertEqual(child._meta.foo, "parent-subclass-foo-update") # type: ignore
        self.assertEqual(child.Meta.bar, "parent-bar")
        self.assertEqual(child._meta.bar, "parent-bar") # type: ignore
        self.assertEqual(child.field1, "child-field1")
        self.assertEqual(child.field2, "child-field2")
        self.assertIn("parent_field", child.Meta.read_only_fields)
        self.assertIn("parent_filter", child.Meta.supported_filtering_params)
        self.assertNotIn("sub_child_field", child.Meta.read_only_fields)
        self.assertNotIn("sub_child_filter", child.Meta.supported_filtering_params)
        self.assertIn("parent_field", child._meta.read_only_fields) # type: ignore
        self.assertIn("parent_filter", child._meta.supported_filtering_params) # type: ignore
        self.assertNotIn("sub_child_field", child._meta.read_only_fields) # type: ignore
        self.assertNotIn("sub_child_filter", child._meta.supported_filtering_params) # type: ignore

        self.assertIsInstance(subchild.Meta, type(StandardModel.Meta))
        self.assertIsInstance(subchild._meta, StandardModel.Meta) # type: ignore
        self.assertEqual(subchild.Meta.foo, "child-subclass-foo-update")
        self.assertEqual(subchild._meta.foo, "child-subclass-foo-update") # type: ignore
        self.assertEqual(subchild.Meta.bar, "subchild-bar")
        self.assertEqual(subchild._meta.bar, "subchild-bar") # type: ignore
        self.assertEqual(subchild.field1, "sub-child-field1")
        self.assertEqual(subchild.field2, "sub-child-field2")
        self.assertEqual(subchild.field3, "sub-child-field3")
        self.assertIn("parent_field", subchild.Meta.read_only_fields)
        self.assertIn("parent_filter", subchild.Meta.supported_filtering_params)
        self.assertIn("sub_child_field", subchild.Meta.read_only_fields)
        self.assertIn("sub_child_filter", subchild.Meta.supported_filtering_params)
        self.assertIn("parent_field", subchild._meta.read_only_fields) # type: ignore
        self.assertIn("parent_filter", subchild._meta.supported_filtering_params) # type: ignore
        self.assertIn("sub_child_field", subchild._meta.read_only_fields) # type: ignore
        self.assertIn("sub_child_filter", subchild._meta.supported_filtering_params) # type: ignore

    def test_auto_create_meta_when_missing(self):
        """Ensure a Meta class is automatically created when missing in a subclass."""

        class AutoMetaModel(StandardModel):
            field3: str

        self.assertTrue(hasattr(AutoMetaModel, "Meta"))
        self.assertTrue(hasattr(AutoMetaModel.Meta, "read_only_fields"))
        self.assertTrue(isinstance(AutoMetaModel.Meta.read_only_fields, set))

    def test_meta_is_unique_per_subclass(self):
        """Ensure that subclasses have separate Meta instances."""

        class ModelA(StandardModel):
            field4: str

            class Meta(StandardModel.Meta):
                read_only_fields: ClassVar[set[str]] = {"field4"}

        class ModelB(StandardModel):
            field5: str

            class Meta(StandardModel.Meta):
                read_only_fields: ClassVar[set[str]] = {"field5"}

        self.assertNotEqual(id(ModelA.Meta), id(ModelB.Meta))
        self.assertIn("field4", ModelA.Meta.read_only_fields)
        self.assertNotIn("field5", ModelA.Meta.read_only_fields)
        self.assertIn("field5", ModelB.Meta.read_only_fields)
        self.assertNotIn("field4", ModelB.Meta.read_only_fields)

    def test_meta_field_aggregation(self):
        """Ensure that Meta attributes aggregate properly from parent classes."""

        class Parent(StandardModel):
            field6: str

            class Meta(StandardModel.Meta):
                read_only_fields: ClassVar[set[str]] = {"parent_readonly"}
                filtering_disabled: ClassVar[set[str]] = {"parent_disabled"}

        class Child(Parent):
            field7: int

            class Meta(Parent.Meta):
                read_only_fields: ClassVar[set[str]] = {"child_readonly"}
                filtering_disabled: ClassVar[set[str]] = {"child_disabled"}

        self.assertIn("parent_readonly", Child.Meta.read_only_fields)
        self.assertIn("child_readonly", Child.Meta.read_only_fields)
        self.assertIn("parent_disabled", Child.Meta.filtering_disabled)
        self.assertIn("child_disabled", Child.Meta.filtering_disabled)

    def test_meta_field_exclusion(self):
        """Ensure filtering_fields excludes filtering_disabled values."""

        class TestModel(StandardModel):
            name: str
            age: int

            class Meta(StandardModel.Meta):
                filtering_disabled: ClassVar[set[str]] = {"age"}

        self.assertIn("name", TestModel.Meta.filtering_fields)
        self.assertNotIn("age", TestModel.Meta.filtering_fields)

if __name__ == "__main__":
    unittest.main()
