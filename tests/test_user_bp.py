import unittest

from app import bcrypt, create_app, db
from app.users.models import User


class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        """Налаштування клієнта тестування перед кожним тестом."""
        self.app = create_app("testing")
        self.client = self.app.test_client()

    def test_greetings_page(self):
        """Тест маршруту /users/hi/<name>."""
        response = self.client.get("/users/hi/John?age=30")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"JOHN", response.data)
        self.assertIn(b"30", response.data)

    def test_admin_page(self):
        """Тест маршруту /users/admin, який перенаправляє."""
        response = self.client.get("/users/admin", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ADMINISTRATOR", response.data)
        self.assertIn(b"45", response.data)

    def test_bcrypt_is_initialized(self):
        password_hash = bcrypt.generate_password_hash("test-password")
        self.assertTrue(bcrypt.check_password_hash(password_hash, "test-password"))
        self.assertFalse(bcrypt.check_password_hash(password_hash, "wrong-password"))


class RegistrationTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def registration_data(self, **overrides):
        data = {
            "username": "new_user",
            "email": "new_user@example.com",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
        }
        data.update(overrides)
        return data

    def add_existing_user(self):
        with self.app.app_context():
            password_hash = bcrypt.generate_password_hash("ExistingPass123").decode("utf-8")
            db.session.add(
                User(
                    username="existing_user",
                    email="existing@example.com",
                    password=password_hash,
                )
            )
            db.session.commit()

    def test_registration_saves_user_with_hashed_password(self):
        response = self.client.post(
            "/users/register", data=self.registration_data(), follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Реєстрація успішна".encode(), response.data)

        with self.app.app_context():
            user = db.session.scalar(
                db.select(User).where(User.username == "new_user")
            )
            self.assertIsNotNone(user)
            self.assertNotEqual(user.password, "StrongPass123")
            self.assertTrue(bcrypt.check_password_hash(user.password, "StrongPass123"))

    def test_registration_rejects_invalid_email(self):
        response = self.client.post(
            "/users/register",
            data=self.registration_data(email="not-an-email"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Введіть коректну адресу електронної пошти.".encode(), response.data)

    def test_registration_rejects_existing_username(self):
        self.add_existing_user()
        response = self.client.post(
            "/users/register",
            data=self.registration_data(username="existing_user"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("користувача вже зайняте.".encode(), response.data)

    def test_registration_rejects_existing_email_case_insensitively(self):
        self.add_existing_user()
        response = self.client.post(
            "/users/register",
            data=self.registration_data(email="EXISTING@example.com"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Ця електронна пошта вже зареєстрована.".encode(), response.data)


if __name__ == "__main__":
    unittest.main()
