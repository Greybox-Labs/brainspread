from django.core.exceptions import ValidationError
from django.test import TestCase

from core.commands.login_command import LoginCommand
from core.forms import LoginForm
from core.test.helpers import UserFactory


class TestLoginCommand(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email="test@example.com")
        cls.user.set_password("testpass123")
        cls.user.save()

    def test_should_login_user_with_valid_credentials(self):
        form_data = {
            "email": "test@example.com",
            "password": "testpass123",
        }
        form = LoginForm(form_data)
        self.assertTrue(form.is_valid())

        command = LoginCommand(form)
        result = command.execute()

        self.assertIn("token", result)
        self.assertIn("user", result)
        self.assertEqual(result["user"]["email"], "test@example.com")

    def test_should_update_timezone_when_provided(self):
        form_data = {
            "email": "test@example.com",
            "password": "testpass123",
            "timezone": "America/New_York",
        }
        form = LoginForm(form_data)
        self.assertTrue(form.is_valid())

        command = LoginCommand(form)
        result = command.execute()

        self.assertEqual(result["user"]["timezone"], "America/New_York")

        self.user.refresh_from_db()
        self.assertEqual(self.user.timezone, "America/New_York")

    def test_should_raise_validation_error_with_invalid_form(self):
        form_data = {"email": "", "password": ""}
        form = LoginForm(form_data)

        command = LoginCommand(form)

        with self.assertRaises(ValidationError):
            command.execute()

    def test_should_raise_validation_error_with_invalid_credentials(self):
        form_data = {
            "email": "test@example.com",
            "password": "wrongpassword",
        }
        form = LoginForm(form_data)

        command = LoginCommand(form)

        with self.assertRaises(ValidationError):
            command.execute()
