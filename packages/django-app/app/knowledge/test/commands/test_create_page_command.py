from django.test import TestCase
from django.core.exceptions import ValidationError
from unittest.mock import Mock, patch

from knowledge.commands import CreatePageCommand
from knowledge.forms import CreatePageForm
from knowledge.models import Page
from ..helpers import UserFactory, PageFactory


class TestCreatePageCommand(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_should_create_page_with_valid_form(self):
        form_data = {
            'title': 'Test Page',
            'content': 'This is test content #tag1 #tag2',
            'slug': 'test-page',
            'is_published': True
        }
        form = CreatePageForm(form_data, user=self.user)
        self.assertTrue(form.is_valid())
        
        command = CreatePageCommand(form, self.user)
        page = command.execute()
        
        self.assertEqual(page.title, 'Test Page')
        self.assertEqual(page.slug, 'test-page')
        self.assertEqual(page.content, 'This is test content #tag1 #tag2')
        self.assertTrue(page.is_published)
        self.assertEqual(page.user, self.user)

    def test_should_auto_generate_slug_when_not_provided(self):
        form_data = {
            'title': 'Test Page With Spaces',
            'content': 'Test content',
            'is_published': True
        }
        form = CreatePageForm(form_data, user=self.user)
        self.assertTrue(form.is_valid())
        
        command = CreatePageCommand(form, self.user)
        page = command.execute()
        
        self.assertEqual(page.slug, 'test-page-with-spaces')

    def test_should_handle_empty_content(self):
        form_data = {
            'title': 'Test Page',
            'is_published': True
        }
        form = CreatePageForm(form_data, user=self.user)
        self.assertTrue(form.is_valid())
        
        command = CreatePageCommand(form, self.user)
        page = command.execute()
        
        self.assertEqual(page.content, '')

    @patch.object(Page, 'set_tags_from_content')
    def test_should_call_set_tags_from_content_when_content_exists(self, mock_set_tags):
        form_data = {
            'title': 'Test Page',
            'content': 'This is test content #tag1 #tag2',
            'is_published': True
        }
        form = CreatePageForm(form_data, user=self.user)
        command = CreatePageCommand(form, self.user)
        page = command.execute()
        
        mock_set_tags.assert_called_once_with('This is test content #tag1 #tag2', self.user)

    @patch.object(Page, 'set_tags_from_content')
    def test_should_not_call_set_tags_from_content_when_no_content(self, mock_set_tags):
        form_data = {
            'title': 'Test Page',
            'is_published': True
        }
        form = CreatePageForm(form_data, user=self.user)
        command = CreatePageCommand(form, self.user)
        page = command.execute()
        
        mock_set_tags.assert_not_called()

    def test_should_raise_validation_error_with_invalid_form(self):
        form = Mock()
        form.is_valid.return_value = False
        form.errors.as_json.return_value = '{"title": ["This field is required."]}'
        
        command = CreatePageCommand(form, self.user)
        
        with self.assertRaises(ValidationError):
            command.execute()

    def test_should_raise_validation_error_with_duplicate_slug(self):
        PageFactory(user=self.user, slug='test-page')
        
        form_data = {
            'title': 'New Page',
            'slug': 'test-page',
            'is_published': True
        }
        form = CreatePageForm(form_data, user=self.user)
        self.assertFalse(form.is_valid())
        
        command = CreatePageCommand(form, self.user)
        
        with self.assertRaises(ValidationError):
            command.execute()

    def test_should_set_default_values_correctly(self):
        form_data = {
            'title': 'Minimal Page'
        }
        form = CreatePageForm(form_data, user=self.user)
        self.assertTrue(form.is_valid())
        
        command = CreatePageCommand(form, self.user)
        page = command.execute()
        
        self.assertEqual(page.title, 'Minimal Page')
        self.assertEqual(page.slug, 'minimal-page')  # Auto-generated
        self.assertEqual(page.content, '')  # Default empty
        self.assertTrue(page.is_published)  # Default True
        self.assertEqual(page.user, self.user)