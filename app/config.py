import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

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


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///data.sqlite")


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
