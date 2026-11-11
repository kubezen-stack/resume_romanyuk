from datetime import datetime
from flask import Blueprint

products_bp = Blueprint(
    "products",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/product",
)

@products_bp.app_template_filter("dt")
def format_datetime(value):
    try:
        return datetime.fromisoformat(value).strftime("%d.%m.%Y %H:%M")
    except (TypeError, ValueError):
        return value or "—"

@products_bp.cli.command("seed")
def seed_products():
    from . import db

    count = db.seed()
    print(f"Додано товарів: {count}" if count else "База не порожня, нічого не додано.")

from . import views
