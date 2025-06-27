from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from core.models import User
from core.test.helpers import UserFactory


class UserAPITestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email="test@example.com")
        cls.user.set_password("testpass123")
        cls.user.save()

    def setUp(self):
        self.client = APIClient()
        self.token = Token.objects.create(user=self.user)

    def test_register_success(self):
        """Test successful user registration"""
        data = {"email": "newuser@example.com", "password": "newpass123"}
        response = self.client.post("/api/auth/register/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertIn("token", response.data["data"])
        self.assertIn("user", response.data["data"])
        self.assertEqual(response.data["data"]["user"]["email"], "newuser@example.com")

        # Verify user was created in database
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

    def test_register_duplicate_email(self):
        """Test registration with existing email"""
        data = {"email": "test@example.com", "password": "newpass123"}  # Already exists
        response = self.client.post("/api/auth/register/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("email", response.data["errors"])

    def test_register_missing_fields(self):
        """Test registration with missing required fields"""
        data = {"email": "test@example.com"}  # Missing password
        response = self.client.post("/api/auth/register/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_login_success(self):
        """Test successful login"""
        data = {"email": "test@example.com", "password": "testpass123"}
        response = self.client.post("/api/auth/login/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("token", response.data["data"])
        self.assertIn("user", response.data["data"])
        self.assertEqual(response.data["data"]["user"]["email"], "test@example.com")

    def test_login_with_timezone(self):
        """Test login with timezone update"""
        data = {
            "email": "test@example.com",
            "password": "testpass123",
            "timezone": "America/New_York",
        }
        response = self.client.post("/api/auth/login/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["user"]["timezone"], "America/New_York")

        # Verify timezone was updated in database
        self.user.refresh_from_db()
        self.assertEqual(self.user.timezone, "America/New_York")

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {"email": "test@example.com", "password": "wrongpassword"}
        response = self.client.post("/api/auth/login/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_login_missing_fields(self):
        """Test login with missing fields"""
        data = {"email": "test@example.com"}  # Missing password
        response = self.client.post("/api/auth/login/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_logout_success(self):
        """Test successful logout"""
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        response = self.client.post("/api/auth/logout/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

        # Verify token was deleted
        self.assertFalse(Token.objects.filter(key=self.token.key).exists())

    def test_logout_unauthenticated(self):
        """Test logout without authentication"""
        response = self.client.post("/api/auth/logout/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_profile_success(self):
        """Test getting current user profile"""
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["user"]["uuid"], str(self.user.uuid))
        self.assertEqual(response.data["data"]["user"]["email"], "test@example.com")

    def test_get_user_profile_unauthenticated(self):
        """Test getting user profile without authentication"""
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_timezone_success(self):
        """Test successful timezone update"""
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        data = {"timezone": "Europe/London"}
        response = self.client.post("/api/auth/update-timezone/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["user"]["timezone"], "Europe/London")
        self.assertEqual(response.data["message"], "Timezone updated successfully")

        # Verify timezone was updated in database
        self.user.refresh_from_db()
        self.assertEqual(self.user.timezone, "Europe/London")

    def test_update_timezone_missing_field(self):
        """Test timezone update with missing timezone"""
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        data = {}
        response = self.client.post("/api/auth/update-timezone/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("timezone", response.data["errors"])

    def test_update_timezone_unauthenticated(self):
        """Test timezone update without authentication"""
        data = {"timezone": "Europe/London"}
        response = self.client.post("/api/auth/update-timezone/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_theme_success(self):
        """Test successful theme update"""
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        data = {"theme": "light"}
        response = self.client.post("/api/auth/update-theme/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["user"]["theme"], "light")
        self.assertEqual(response.data["message"], "Theme updated successfully")

        # Verify theme was updated in database
        self.user.refresh_from_db()
        self.assertEqual(self.user.theme, "light")

    def test_update_theme_invalid_choice(self):
        """Test theme update with invalid theme choice"""
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        data = {"theme": "rainbow"}  # Invalid choice
        response = self.client.post("/api/auth/update-theme/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("theme", response.data["errors"])

    def test_update_theme_missing_field(self):
        """Test theme update with missing theme"""
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        data = {}
        response = self.client.post("/api/auth/update-theme/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("theme", response.data["errors"])

    def test_update_theme_unauthenticated(self):
        """Test theme update without authentication"""
        data = {"theme": "light"}
        response = self.client.post("/api/auth/update-theme/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
