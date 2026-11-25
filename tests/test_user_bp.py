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

    def test_registration_page_loads(self):
        response = self.client.get("/users/register")
        self.assertEqual(response.status_code, 200)
        for field in (b'name="username"', b'name="email"', b'name="password"', b'name="confirm_password"'):
            self.assertIn(field, response.data)

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


class LoginTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            password_hash = bcrypt.generate_password_hash("LoginPass123").decode("utf-8")
            db.session.add(
                User(
                    username="login_user",
                    email="login_user@example.com",
                    password=password_hash,
                )
            )
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_login_page_loads(self):
        response = self.client.get("/users/login")
        self.assertEqual(response.status_code, 200)
        for field in (b'name="username"', b'name="password"', b'name="remember"'):
            self.assertIn(field, response.data)

    def test_login_accepts_correct_password_and_sets_session(self):
        response = self.client.post(
            "/users/login",
            data={"username": "login_user", "password": "LoginPass123"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Ви успішно увійшли.".encode(), response.data)
        self.assertIn("login_user".encode(), response.data)
        with self.client.session_transaction() as session_data:
            self.assertEqual(session_data["_user_id"], "1")

    def test_authenticated_user_is_redirected_from_registration(self):
        self.client.post(
            "/users/login",
            data={"username": "login_user", "password": "LoginPass123"},
        )
        response = self.client.get("/users/register")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/users/profile"))

    def test_nav_shows_login_and_registration_for_guests(self):
        response = self.client.get("/homepage")
        self.assertIn(b'href="/users/login"', response.data)
        self.assertIn(b'href="/users/register"', response.data)
        self.assertNotIn(b'href="/users/profile"', response.data)
        self.assertNotIn(b'action="/users/logout"', response.data)

    def test_nav_shows_profile_and_logout_for_authenticated_users(self):
        self.client.post(
            "/users/login",
            data={"username": "login_user", "password": "LoginPass123"},
        )
        response = self.client.get("/homepage")
        self.assertIn(b'href="/users/profile"', response.data)
        self.assertIn(b'action="/users/logout"', response.data)
        self.assertNotIn(b'href="/users/login"', response.data)
        self.assertNotIn(b'href="/users/register"', response.data)

    def test_login_rejects_incorrect_password(self):
        response = self.client.post(
            "/users/login",
            data={"username": "login_user", "password": "WrongPass123"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("користувача або пароль.".encode(), response.data)
        with self.client.session_transaction() as session_data:
            self.assertNotIn("_user_id", session_data)

    def test_login_rejects_unknown_username(self):
        response = self.client.post(
            "/users/login",
            data={"username": "unknown_user", "password": "LoginPass123"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("користувача або пароль.".encode(), response.data)
        with self.client.session_transaction() as session_data:
            self.assertNotIn("_user_id", session_data)

    def test_logout_clears_flask_login_session(self):
        self.client.post(
            "/users/login",
            data={"username": "login_user", "password": "LoginPass123"},
        )
        response = self.client.post("/users/logout", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Ви вийшли з системи.".encode(), response.data)
        with self.client.session_transaction() as session_data:
            self.assertNotIn("_user_id", session_data)

    def test_protected_pages_redirect_unauthenticated_users_to_login(self):
        for path in ("/users/profile", "/users/list"):
            with self.subTest(path=path):
                response = self.client.get(path, follow_redirects=True)
                self.assertEqual(response.status_code, 200)
                self.assertIn("Please log in to access this page.".encode(), response.data)


class UserListTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_user_list_shows_users_and_count_without_passwords(self):
        with self.app.app_context():
            db.session.add_all(
                [
                    User(
                        username="first_user",
                        email="first@example.com",
                        password=bcrypt.generate_password_hash("FirstPass123").decode("utf-8"),
                    ),
                    User(
                        username="second_user",
                        email="second@example.com",
                        password=bcrypt.generate_password_hash("SecondPass123").decode("utf-8"),
                    ),
                ]
            )
            db.session.commit()

        self.client.post(
            "/users/login",
            data={"username": "first_user", "password": "FirstPass123"},
        )
        response = self.client.get("/users/list")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Список користувачів (2)".encode(), response.data)
        self.assertIn("first_user".encode(), response.data)
        self.assertIn("first@example.com".encode(), response.data)
        self.assertNotIn(b"$2b$", response.data)

    def test_user_list_requires_authentication_when_empty(self):
        response = self.client.get("/users/list")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].startswith("/users/login?"))


if __name__ == "__main__":
    unittest.main()
