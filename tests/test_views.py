import unittest

from app import app


class MainViewsTestCase(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_resume_pages(self):
        for url in ("/", "/resume"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertIn("Резюме".encode(), response.data)

    def test_contacts_page(self):
        response = self.client.get("/contacts")
        self.assertEqual(response.status_code, 200)

    def test_homepage(self):
        response = self.client.get("/homepage")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
