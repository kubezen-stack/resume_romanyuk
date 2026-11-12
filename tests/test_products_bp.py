import os
import tempfile
import unittest

from app import create_app
from app.products import db


class ProductsBlueprintTestCase(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app("testing")
        self.app.config.update(PRODUCTS_DB_FILE=os.path.join(self.tmp.name, "products.json"))
        self.client = self.app.test_client()
        with self.app.app_context():
            db.seed()

    def tearDown(self):
        self.tmp.cleanup()

    def test_products_list(self):
        response = self.client.get("/product/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Laptop", response.data)
        self.assertIn(b"Phone", response.data)
        self.assertIn(b"PC", response.data)

    def test_product_detail(self):
        response = self.client.get("/product/2")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Phone", response.data)
        self.assertIn(b"800", response.data)

    def test_product_not_found(self):
        self.assertEqual(self.client.get("/product/999").status_code, 404)


if __name__ == "__main__":
    unittest.main()