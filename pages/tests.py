from django.test import TestCase


class HomePageTests(TestCase):
    def test_home_returns_200(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
