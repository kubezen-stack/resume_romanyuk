import json
import os
import re
import tempfile
import unittest

from app import create_app


class ContactFormTestCase(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.tmp.name, "logs", "contacts.log")
        self.app = create_app("testing")
        self.app.config.update(CONTACT_LOG_FILE=self.log_path)
        self.client = self.app.test_client()
        self.valid = {
            "name": "Іван Петренко",
            "email": "ivan@example.com",
            "topic": "cooperation",
            "message": "Доброго дня, хочу обговорити співпрацю.",
        }

    def tearDown(self):
        self.tmp.cleanup()

    def test_get_renders_form_fields(self):
        response = self.client.get("/contacts")
        self.assertEqual(response.status_code, 200)
        for field in (b'name="name"', b'name="email"', b'<select', b'<textarea', b'type="submit"'):
            self.assertIn(field, response.data)

    def test_valid_post_redirects_logs_and_flashes(self):
        response = self.client.post("/contacts", data=self.valid)
        # Post/Redirect/Get
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/contacts"))

        with open(self.log_path, encoding="utf-8") as f:
            lines = f.read().strip().splitlines()
        self.assertEqual(len(lines), 1)
        entry = json.loads(lines[0].split(" | ", 1)[1])
        self.assertEqual(entry["email"], "ivan@example.com")
        self.assertEqual(entry["topic"], "Співпраця")

        page = self.client.get("/contacts")
        self.assertIn("надіслано і збережено".encode(), page.data)
        self.assertIn(b"alert-success", page.data)
        # повторне оновлення сторінки не повторює відправку
        self.assertNotIn("надіслано і збережено".encode(), self.client.get("/contacts").data)

    def test_second_submit_appends_to_log(self):
        self.client.post("/contacts", data=self.valid)
        self.client.post("/contacts", data=self.valid)
        with open(self.log_path, encoding="utf-8") as f:
            self.assertEqual(len(f.read().strip().splitlines()), 2)

    def test_invalid_data_shows_errors_and_does_not_log(self):
        response = self.client.post(
            "/contacts", data={"name": "І", "email": "not-an-email", "topic": "", "message": "коротко"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"alert-danger", response.data)
        self.assertIn(b"invalid-feedback", response.data)
        self.assertIn("від 2 до 50 символів".encode(), response.data)
        self.assertIn("Оберіть тему".encode(), response.data)
        self.assertFalse(os.path.exists(self.log_path))

    def test_empty_post(self):
        response = self.client.post("/contacts", data={})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Вкажіть ім".encode(), response.data)
        self.assertIn("Вкажіть email".encode(), response.data)

    def test_log_failure_shows_error_flash(self):
        # шлях до "файлу" вказує на існуючу директорію -> запис неможливий
        self.app.config["CONTACT_LOG_FILE"] = self.tmp.name
        response = self.client.post("/contacts", data=self.valid)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Не вдалося зберегти".encode(), response.data)
        self.assertIn(b"alert-danger", response.data)

    def test_csrf_protection(self):
        self.app.config["WTF_CSRF_ENABLED"] = True
        response = self.client.post("/contacts", data=self.valid)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(os.path.exists(self.log_path))

        page = self.client.get("/contacts")
        token = re.search(rb'name="csrf_token"[^>]*value="([^"]+)"', page.data).group(1).decode()
        response = self.client.post("/contacts", data={**self.valid, "csrf_token": token})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(os.path.exists(self.log_path))


if __name__ == "__main__":
    unittest.main()
