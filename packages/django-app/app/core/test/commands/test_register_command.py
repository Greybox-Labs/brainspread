import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase

from core.commands.register_command import RegisterCommand
from core.forms import RegisterForm
from core.test.helpers import UserFactory


class TestRegisterCommand(TestCase):
    def test_should_create_user_with_valid_form(self):
        form_data = {
            "email": "test@example.com",
            "password": "testpass123",
        }
        form = RegisterForm(form_data)
        self.assertTrue(form.is_valid())

        command = RegisterCommand(form)
        result = command.execute()

        self.assertIn("token", result)
        self.assertIn("user", result)
        self.assertEqual(result["user"]["email"], "test@example.com")

        from core.models import User

        user = User.objects.get(email="test@example.com")
        self.assertTrue(user.is_active)

    def test_should_raise_validation_error_with_invalid_form(self):
        form_data = {"email": "", "password": ""}
        form = RegisterForm(form_data)

        command = RegisterCommand(form)

        with self.assertRaises(ValidationError):
            command.execute()

    def test_should_raise_validation_error_with_duplicate_email(self):
        UserFactory(email="test@example.com")

        form_data = {
            "email": "test@example.com",
            "password": "testpass123",
        }
        form = RegisterForm(form_data)

        command = RegisterCommand(form)

        with self.assertRaises(ValidationError):
            command.execute()
