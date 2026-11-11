import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = "d7e19042160471160caea8bc50fc5e1adad918417ae2007c6c88118a82147b43"
DEBUG = True

CONTACT_LOG_FILE = os.path.join(BASE_DIR, "logs", "contacts.log")

PRODUCTS_DB_FILE = os.path.join(BASE_DIR, "data", "products.json")
PRODUCT_UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "products", "static", "uploads")
MAX_IMAGE_SIZE = 2 * 1024 * 1024
MAX_CONTENT_LENGTH = 3 * 1024 * 1024
PRODUCT_CATEGORIES = [
    ("electronics", "Електроніка"),
    ("computers", "Комп'ютери"),
    ("phones", "Телефони"),
    ("accessories", "Аксесуари"),
    ("other", "Інше"),
]
