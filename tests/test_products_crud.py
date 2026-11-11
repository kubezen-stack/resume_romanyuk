import io
import os
import tempfile
import unittest

from app import app
from app.products import db


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 64


class ProductsBaseTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "data", "products.json")
        self.upload_dir = os.path.join(self.tmp.name, "static", "uploads")
        self._old = {
            k: app.config.get(k)
            for k in ("PRODUCTS_DB_FILE", "PRODUCT_UPLOAD_FOLDER", "WTF_CSRF_ENABLED", "TESTING", "MAX_IMAGE_SIZE")
        }
        app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            PRODUCTS_DB_FILE=self.db_path,
            PRODUCT_UPLOAD_FOLDER=self.upload_dir,
        )
        self.client = app.test_client()

    def tearDown(self):
        app.config.update(self._old)
        self.tmp.cleanup()

    def make_product(self, **extra):
        data = {"name": "Laptop", "content": "Опис ноутбука", "price": 1200.0,
                "category": "computers", "quantity": 5, "image": ""}
        data.update(extra)
        with app.app_context():
            return db.create_product(data)


class ProductsReadTestCase(ProductsBaseTestCase):

    def test_list_empty(self):
        response = self.client.get("/product")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Товарів поки немає".encode(), response.data)

    def test_list_shows_product_fields(self):
        self.make_product()
        response = self.client.get("/product/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Laptop", response.data)
        self.assertIn("Комп&#39;ютери".encode(), response.data)  # категорія
        self.assertIn(b"1200.00", response.data)               # ціна
        self.assertIn("5 шт.".encode(), response.data)         # кількість
        self.assertIn(b"no-image.svg", response.data)          # відсутнє зображення

    def test_detail(self):
        product = self.make_product()
        response = self.client.get(f"/product/{product['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Опис ноутбука".encode(), response.data)

    def test_detail_not_found(self):
        response = self.client.get("/product/999")
        self.assertEqual(response.status_code, 404)
        self.assertIn("404".encode(), response.data)

    def test_ids_are_unique_and_created_at_set(self):
        a, b = self.make_product(name="A"), self.make_product(name="B")
        self.assertNotEqual(a["id"], b["id"])
        self.assertTrue(a["created_at"])

    def test_data_persists_between_connections(self):
        self.make_product(name="Persist")
        with app.app_context():
            names = [p["name"] for p in db.list_products()]
        self.assertEqual(names, ["Persist"])
        self.assertTrue(os.path.exists(self.db_path))


class ProductsCreateTestCase(ProductsBaseTestCase):

    def valid_data(self, **extra):
        data = {"name": "Phone", "content": "Смартфон", "price": "800.50",
                "category": "phones", "quantity": "12"}
        data.update(extra)
        return data

    def test_add_form_renders(self):
        response = self.client.get("/product/add")
        self.assertEqual(response.status_code, 200)
        for field in (b'name="name"', b"<textarea", b'rows="5"', b'cols="40"', b'name="price"',
                      b"<select", b'name="quantity"', b'type="submit"'):
            self.assertIn(field, response.data)

    def test_add_valid_redirects_saves_and_flashes(self):
        response = self.client.post("/product/add", data=self.valid_data())
        self.assertEqual(response.status_code, 302)  # Post/Redirect/Get
        self.assertTrue(response.headers["Location"].endswith("/product/1"))

        with app.app_context():
            product = db.get_product(1)
        self.assertEqual(product["name"], "Phone")
        self.assertEqual(product["price"], 800.5)
        self.assertEqual(product["quantity"], 12)
        self.assertEqual(product["image"], "")
        self.assertTrue(product["created_at"])

        page = self.client.get("/product/1")
        self.assertIn(b"alert-success", page.data)
        self.assertNotIn(b"alert-success", self.client.get("/product/1").data)  # flash показується один раз

    def test_price_accepts_comma(self):
        self.client.post("/product/add", data=self.valid_data(price="10,5"))
        with app.app_context():
            self.assertEqual(db.get_product(1)["price"], 10.5)

    def test_invalid_data_shows_errors_and_saves_nothing(self):
        bad = {"name": "ab", "content": "", "price": "-5", "category": "", "quantity": "-1"}
        response = self.client.post("/product/add", data=bad)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"alert-danger", response.data)
        self.assertIn(b"invalid-feedback", response.data)
        for text in ("від 3 до 100", "Вкажіть опис", "Ціна має бути додатною", "Оберіть категорію", "від'ємною"):
            self.assertIn(text.replace("'", "&#39;").encode(), response.data)
        with app.app_context():
            self.assertEqual(db.list_products(), [])

    def test_validation_rules(self):
        cases = {
            "price": ["0", "abc", "1.999", ""],
            "quantity": ["1.5", "x", ""],
            "name": ["  ab  ", ""],
            "category": ["unknown"],
        }
        for field, values in cases.items():
            for value in values:
                response = self.client.post("/product/add", data=self.valid_data(**{field: value}))
                self.assertEqual(response.status_code, 200, f"{field}={value!r}")
        with app.app_context():
            self.assertEqual(db.list_products(), [])

    def test_zero_quantity_is_allowed(self):
        response = self.client.post("/product/add", data=self.valid_data(quantity="0"))
        self.assertEqual(response.status_code, 302)

    def test_csrf_protection(self):
        import re

        app.config["WTF_CSRF_ENABLED"] = True
        response = self.client.post("/product/add", data=self.valid_data())
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            self.assertEqual(db.list_products(), [])

        page = self.client.get("/product/add")
        token = re.search(rb'name="csrf_token"[^>]*value="([^"]+)"', page.data).group(1).decode()
        response = self.client.post("/product/add", data={**self.valid_data(), "csrf_token": token})
        self.assertEqual(response.status_code, 302)


class ImageHelpers:

    def post_with_image(self, content, filename, **extra):
        data = {"name": "Phone", "content": "Смартфон", "price": "800", "category": "phones",
                "quantity": "1", "image": (io.BytesIO(content), filename)}
        data.update(extra)
        return self.client.post("/product/add", data=data, content_type="multipart/form-data")

    def uploaded_files(self):
        return os.listdir(self.upload_dir) if os.path.isdir(self.upload_dir) else []


class ProductsImageUploadTestCase(ImageHelpers, ProductsBaseTestCase):

    def test_png_and_jpg_accepted_with_uuid_names(self):
        for content, name in ((PNG_BYTES, "my photo.PNG"), (JPG_BYTES, "pic.jpeg"), (JPG_BYTES, "x.jpg")):
            self.assertEqual(self.post_with_image(content, name).status_code, 302)
        files = self.uploaded_files()
        self.assertEqual(len(files), 3)
        for f in files:
            self.assertRegex(f, r"^[0-9a-f]{32}\.(png|jpg|jpeg)$")
            self.assertNotIn("photo", f)

    def test_relative_path_stored_and_image_shown(self):
        self.post_with_image(PNG_BYTES, "a.png")
        with app.app_context():
            image = db.get_product(1)["image"]
        self.assertRegex(image, r"^uploads/[0-9a-f]{32}\.png$")
        self.assertTrue(os.path.isfile(os.path.join(self.tmp.name, "static", image)))
        for url in ("/product/", "/product/1"):
            page = self.client.get(url)
            self.assertIn(image.encode(), page.data)
            self.assertNotIn(b"no-image.svg", page.data)

    def test_wrong_extension_rejected(self):
        for name in ("a.gif", "a.txt", "a.png.exe", "noext"):
            response = self.post_with_image(PNG_BYTES, name)
            self.assertEqual(response.status_code, 200, name)
            self.assertIn("Дозволені лише формати".encode(), response.data)
        self.assertEqual(self.uploaded_files(), [])
        with app.app_context():
            self.assertEqual(db.list_products(), [])

    def test_fake_image_content_rejected(self):
        response = self.post_with_image(b"<?php echo 1; ?>", "evil.png")
        self.assertEqual(response.status_code, 200)
        self.assertIn("не є коректним зображенням".encode(), response.data)
        self.assertEqual(self.uploaded_files(), [])

    def test_too_large_file_rejected(self):
        app.config["MAX_IMAGE_SIZE"] = 100
        response = self.post_with_image(PNG_BYTES + b"\x00" * 200, "big.png")
        self.assertEqual(response.status_code, 200)
        self.assertIn("завелике".encode(), response.data)
        self.assertEqual(self.uploaded_files(), [])

    def test_request_over_content_length_redirects_with_flash(self):
        old = app.config["MAX_CONTENT_LENGTH"]
        app.config["MAX_CONTENT_LENGTH"] = 200
        try:
            response = self.post_with_image(PNG_BYTES + b"\x00" * 5000, "big.png")
        finally:
            app.config["MAX_CONTENT_LENGTH"] = old
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.uploaded_files(), [])

    def test_missing_image_file_on_disk_shows_placeholder(self):
        self.make_product(image="uploads/does-not-exist.png")
        self.assertIn(b"no-image.svg", self.client.get("/product/1").data)


class ProductsEditTestCase(ImageHelpers, ProductsBaseTestCase):

    def edit_data(self, **extra):
        data = {"name": "Laptop Pro", "content": "Новий опис", "price": "1500.99",
                "category": "electronics", "quantity": "7"}
        data.update(extra)
        return data

    def test_edit_form_prefilled(self):
        self.make_product(name="Laptop", price=1200.5, quantity=5)
        response = self.client.get("/product/1/edit")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'value="Laptop"', response.data)
        self.assertIn(b'value="1200.50"', response.data)
        self.assertIn(b'value="5"', response.data)
        self.assertIn("Опис ноутбука".encode(), response.data)
        self.assertIn(b'<option selected value="computers"', response.data)

    def test_edit_not_found(self):
        self.assertEqual(self.client.get("/product/999/edit").status_code, 404)
        self.assertEqual(self.client.post("/product/999/edit", data=self.edit_data()).status_code, 404)

    def test_edit_updates_fields_keeps_id_and_created_at(self):
        original = self.make_product()
        response = self.client.post("/product/1/edit", data=self.edit_data())
        self.assertEqual(response.status_code, 302)  # PRG
        self.assertTrue(response.headers["Location"].endswith("/product/1"))
        with app.app_context():
            product = db.get_product(1)
        self.assertEqual(product["name"], "Laptop Pro")
        self.assertEqual(product["price"], 1500.99)
        self.assertEqual(product["category"], "electronics")
        self.assertEqual(product["quantity"], 7)
        self.assertEqual(product["id"], original["id"])
        self.assertEqual(product["created_at"], original["created_at"])
        self.assertIn(b"alert-success", self.client.get("/product/1").data)

    def test_edit_invalid_does_not_change_data(self):
        self.make_product()
        response = self.client.post("/product/1/edit", data=self.edit_data(name="ab", price="0"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"invalid-feedback", response.data)
        with app.app_context():
            self.assertEqual(db.get_product(1)["name"], "Laptop")

    def test_edit_keeps_previous_image_when_no_file(self):
        self.post_with_image(PNG_BYTES, "a.png")
        with app.app_context():
            old = db.get_product(1)["image"]
        self.client.post("/product/1/edit", data=self.edit_data())
        with app.app_context():
            self.assertEqual(db.get_product(1)["image"], old)
        self.assertEqual(len(self.uploaded_files()), 1)

    def test_edit_replaces_image_and_removes_old_file(self):
        self.post_with_image(PNG_BYTES, "a.png")
        with app.app_context():
            old = db.get_product(1)["image"]
        data = {**self.edit_data(), "image": (io.BytesIO(JPG_BYTES), "b.jpg")}
        response = self.client.post("/product/1/edit", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 302)
        with app.app_context():
            new = db.get_product(1)["image"]
        self.assertNotEqual(new, old)
        self.assertTrue(new.endswith(".jpg"))
        self.assertEqual(self.uploaded_files(), [os.path.basename(new)])

    def test_edit_invalid_image_keeps_old(self):
        self.post_with_image(PNG_BYTES, "a.png")
        data = {**self.edit_data(), "image": (io.BytesIO(b"x"), "b.gif")}
        response = self.client.post("/product/1/edit", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.uploaded_files()), 1)


class ProductsDeleteTestCase(ImageHelpers, ProductsBaseTestCase):

    def test_delete_removes_product_and_redirects(self):
        self.make_product()
        self.make_product(name="Other")
        response = self.client.post("/product/1/delete")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/product"))
        with app.app_context():
            self.assertEqual([p["name"] for p in db.list_products()], ["Other"])
        self.assertIn(b"alert-success", self.client.get("/product/").data)
        self.assertEqual(self.client.get("/product/1").status_code, 404)

    def test_delete_removes_image_file(self):
        self.post_with_image(PNG_BYTES, "a.png")
        self.assertEqual(len(self.uploaded_files()), 1)
        self.client.post("/product/1/delete")
        self.assertEqual(self.uploaded_files(), [])

    def test_delete_only_via_post(self):
        self.make_product()
        self.assertEqual(self.client.get("/product/1/delete").status_code, 405)
        with app.app_context():
            self.assertIsNotNone(db.get_product(1))

    def test_delete_not_found(self):
        self.assertEqual(self.client.post("/product/999/delete").status_code, 404)

    def test_delete_requires_csrf_token(self):
        self.make_product()
        app.config["WTF_CSRF_ENABLED"] = True
        response = self.client.post("/product/1/delete")
        self.assertEqual(response.status_code, 302)
        with app.app_context():
            self.assertIsNotNone(db.get_product(1))  # товар не видалено

    def test_confirmation_modal_present(self):
        self.make_product()
        for url in ("/product/", "/product/1"):
            page = self.client.get(url)
            self.assertIn(b'id="deleteModal"', page.data)
            self.assertIn(b'data-action="/product/1/delete"', page.data)

    def test_ids_not_reused_inside_session_data_intact(self):
        self.make_product(name="A")
        self.make_product(name="B")
        self.client.post("/product/1/delete")
        with app.app_context():
            self.assertEqual([p["id"] for p in db.list_products()], [2])


if __name__ == "__main__":
    unittest.main()
