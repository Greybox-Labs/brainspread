from django.test import TestCase
from factory import Faker, SubFactory
from factory.django import DjangoModelFactory

from core.test.helpers import UserFactory
from knowledge.test.helpers import BlockFactory, PageFactory
from tagging.commands import GetTagContentCommand
from tagging.forms import GetTagContentForm
from tagging.models import Tag, TaggedItem


class TagFactory(DjangoModelFactory):
    name = Faker("word")
    color = "#007bff"

    class Meta:
        model = Tag


class TaggedItemFactory(DjangoModelFactory):
    tag = SubFactory(TagFactory)
    created_by = SubFactory(UserFactory)

    class Meta:
        model = TaggedItem


class TestGetTagContentCommand(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.other_user = UserFactory()
        cls.tag = TagFactory(name="test-tag")

        cls.page = PageFactory(user=cls.user)
        cls.block = BlockFactory(user=cls.user, page=cls.page)

        cls.other_page = PageFactory(user=cls.other_user)
        cls.other_block = BlockFactory(user=cls.other_user, page=cls.other_page)

    def test_get_tag_content_with_tagged_content(self):
        """Test getting tag content when user has tagged content"""
        TaggedItemFactory(tag=self.tag, content_object=self.page, created_by=self.user)
        TaggedItemFactory(tag=self.tag, content_object=self.block, created_by=self.user)

        form_data = {"user": self.user.id, "tag_name": "test-tag"}
        form = GetTagContentForm(form_data)
        self.assertTrue(form.is_valid())

        command = GetTagContentCommand(form)
        result = command.execute()

        self.assertIsNotNone(result)
        self.assertEqual(result["tag"], self.tag)
        self.assertIn(self.page, result["pages"])
        self.assertIn(self.block, result["blocks"])

    def test_get_tag_content_with_no_user_tagged_content(self):
        """Test getting tag content when user has no tagged content"""
        TaggedItemFactory(
            tag=self.tag, content_object=self.other_page, created_by=self.other_user
        )

        form_data = {"user": self.user.id, "tag_name": "test-tag"}
        form = GetTagContentForm(form_data)
        self.assertTrue(form.is_valid())

        command = GetTagContentCommand(form)
        result = command.execute()

        self.assertIsNone(result)

    def test_get_tag_content_nonexistent_tag(self):
        """Test getting content for a tag that doesn't exist"""
        form_data = {"user": self.user.id, "tag_name": "nonexistent-tag"}
        form = GetTagContentForm(form_data)
        self.assertTrue(form.is_valid())

        command = GetTagContentCommand(form)
        result = command.execute()

        self.assertIsNone(result)

    def test_get_tag_content_filters_by_user(self):
        """Test that tag content is filtered by user"""
        TaggedItemFactory(tag=self.tag, content_object=self.page, created_by=self.user)
        TaggedItemFactory(
            tag=self.tag, content_object=self.other_page, created_by=self.other_user
        )

        form_data = {"user": self.user.id, "tag_name": "test-tag"}
        form = GetTagContentForm(form_data)
        self.assertTrue(form.is_valid())

        command = GetTagContentCommand(form)
        result = command.execute()

        self.assertIsNotNone(result)
        self.assertIn(self.page, result["pages"])
        self.assertNotIn(self.other_page, result["pages"])

    def test_form_validation_missing_user(self):
        """Test form validation when user is missing"""
        form_data = {"tag_name": "test-tag"}
        form = GetTagContentForm(form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("user", form.errors)

    def test_form_validation_missing_tag_name(self):
        """Test form validation when tag_name is missing"""
        form_data = {"user": self.user.id}
        form = GetTagContentForm(form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("tag_name", form.errors)

    def test_form_validation_empty_tag_name(self):
        """Test form validation when tag_name is empty"""
        form_data = {"user": self.user.id, "tag_name": "   "}
        form = GetTagContentForm(form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("tag_name", form.errors)

    def test_form_validation_valid_data(self):
        """Test form validation with valid data"""
        form_data = {"user": self.user.id, "tag_name": "test-tag"}
        form = GetTagContentForm(form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["user"], self.user)
        self.assertEqual(form.cleaned_data["tag_name"], "test-tag")

    def test_form_validation_strips_whitespace(self):
        """Test that form validation strips whitespace from tag_name"""
        form_data = {"user": self.user.id, "tag_name": "  test-tag  "}
        form = GetTagContentForm(form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["tag_name"], "test-tag")
