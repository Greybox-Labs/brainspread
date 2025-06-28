from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from core.test.helpers import UserFactory
from knowledge.models import Page


class BasicKnowledgeAPITestCase(TestCase):
    """Basic API tests that demonstrate testing at the view layer instead of command layer."""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email="test@example.com")
        cls.user.set_password("testpass123")
        cls.user.save()

    def setUp(self):
        self.client = APIClient()
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_create_page_api_success(self):
        """Test page creation through API - replaces CreatePageCommand test"""
        data = {"title": "API Test Page", "content": "Test content"}
        response = self.client.post("/knowledge/api/pages/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["title"], "API Test Page")
        self.assertEqual(response.data["data"]["slug"], "api-test-page")

        # Verify page was actually created in database
        self.assertTrue(
            Page.objects.filter(title="API Test Page", user=self.user).exists()
        )

    def test_create_page_api_validation_error(self):
        """Test page creation validation through API - replaces command validation tests"""
        data = {"content": "Missing title"}  # No title provided
        response = self.client.post("/knowledge/api/pages/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("errors", response.data)

    def test_create_page_api_authentication_required(self):
        """Test API authentication - replaces manual auth tests in commands"""
        self.client.credentials()  # Remove authentication

        data = {"title": "Unauthorized Page"}
        response = self.client.post("/knowledge/api/pages/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_pages_api_user_isolation(self):
        """Test user data isolation through API - replaces repository/command user filtering tests"""
        # Create a clean user for this test to avoid interference
        clean_user = UserFactory(email="clean@example.com")
        clean_token = Token.objects.create(user=clean_user)

        # Create page as clean user
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {clean_token.key}")
        data = {"title": "Clean User Page"}
        self.client.post("/knowledge/api/pages/", data, format="json")

        # Create second user and switch to them
        other_user = UserFactory(email="isolated@example.com")
        other_token = Token.objects.create(user=other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {other_token.key}")

        # Create page as second user
        data = {"title": "Isolated User Page"}
        self.client.post("/knowledge/api/pages/", data, format="json")

        # List pages - should only see second user's page
        response = self.client.get("/knowledge/api/pages/list/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should only see one page (second user's page)
        pages_data = response.data["data"]
        pages = pages_data["pages"]
        self.assertEqual(len(pages), 1)

        # Verify it's the right page
        page_titles = [page["title"] for page in pages]
        self.assertIn("Isolated User Page", page_titles)
        self.assertNotIn("Clean User Page", page_titles)

    def test_historical_data_api_works(self):
        """Test historical data endpoint works - replaces GetHistoricalDataCommand test"""
        # Create some test data first
        page_data = {"title": "History Test Page"}
        self.client.post("/knowledge/api/pages/", page_data, format="json")

        # Get historical data
        response = self.client.get("/knowledge/api/historical/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        # The response contains 'pages', 'blocks', and 'date_range' keys
        self.assertIn("pages", response.data["data"])
        self.assertIn("blocks", response.data["data"])

    def test_api_integration_vs_unit_testing_approach(self):
        """
        This test demonstrates the benefit of API-level testing vs command testing.

        Instead of testing:
        - CreatePageCommand.execute()
        - GetUserPagesCommand.execute()
        - UpdatePageCommand.execute()

        We test the full workflow through the API, which:
        1. Tests the actual user interface
        2. Tests form validation
        3. Tests authentication/authorization
        4. Tests the full request/response cycle
        5. Tests integration between all layers
        """

        # 1. Create page through API (tests CreatePageCommand + form + view + auth)
        create_data = {"title": "Integration Test Page"}
        create_response = self.client.post(
            "/knowledge/api/pages/", create_data, format="json"
        )
        self.assertEqual(create_response.status_code, status.HTTP_200_OK)
        page_uuid = create_response.data["data"]["uuid"]

        # 2. List pages through API (tests GetUserPagesCommand + form + view + auth)
        list_response = self.client.get("/knowledge/api/pages/list/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        # Find our specific page (there may be other pages from other tests)
        found_page = None
        pages_data = list_response.data["data"]
        pages = pages_data["pages"]
        for page in pages:
            if page["title"] == "Integration Test Page":
                found_page = page
                break
        self.assertIsNotNone(
            found_page, "Integration Test Page should be found in the list"
        )

        # 3. Update page through API (tests UpdatePageCommand + form + view + auth)
        update_data = {"page": page_uuid, "title": "Updated Integration Test"}
        update_response = self.client.put(
            "/knowledge/api/pages/update/", update_data, format="json"
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            update_response.data["data"]["title"], "Updated Integration Test"
        )

        # This single test replaces multiple command tests and provides better coverage
        # because it tests the complete user workflow, not just isolated business logic.
