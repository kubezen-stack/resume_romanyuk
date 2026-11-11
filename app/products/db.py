import os
from contextlib import contextmanager
from datetime import datetime

from flask import current_app
from tinydb import TinyDB
from tinydb.table import Document

TABLE_NAME = "products"


def init_db(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    db = TinyDB(path, encoding="utf-8", ensure_ascii=False, indent=2)
    try:
        db.table(TABLE_NAME)
    finally:
        db.close()


@contextmanager
def _table():
    path = current_app.config["PRODUCTS_DB_FILE"]
    init_db(path)
    db = TinyDB(path, encoding="utf-8", ensure_ascii=False, indent=2)
    try:
        yield db.table(TABLE_NAME)
    finally:
        db.close()


def list_products():
    with _table() as table:
        return sorted((dict(d) for d in table.all()), key=lambda p: p["id"])


def get_product(product_id):
    with _table() as table:
        doc = table.get(doc_id=product_id)
        return dict(doc) if doc is not None else None


def create_product(data):
    with _table() as table:
        new_id = max((d.doc_id for d in table.all()), default=0) + 1
        product = {
            "id": new_id,
            **data,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        table.insert(Document(product, doc_id=new_id))
        return product


def update_product(product_id, data):
    data = {k: v for k, v in data.items() if k not in ("id", "created_at")}
    with _table() as table:
        if not table.contains(doc_id=product_id):
            return None
        table.update(data, doc_ids=[product_id])
        return dict(table.get(doc_id=product_id))


def delete_product(product_id):
    with _table() as table:
        doc = table.get(doc_id=product_id)
        if doc is None:
            return None
        table.remove(doc_ids=[product_id])
        return dict(doc)


SEED = [
    {"name": "Laptop", "price": 1200.0, "category": "computers", "quantity": 5,
     "content": "Потужний ноутбук з процесором Intel Core i7, 16 ГБ оперативної пам'яті та SSD на 512 ГБ."},
    {"name": "Phone", "price": 800.0, "category": "phones", "quantity": 12,
     "content": "Смартфон із 6.5-дюймовим OLED-дисплеєм, подвійною камерою та акумулятором на 5000 мА·год."},
    {"name": "PC", "price": 1800.0, "category": "computers", "quantity": 3,
     "content": "Настільний комп'ютер для ігор або роботи з графікою: RTX 4070, 32 ГБ RAM, 1 ТБ SSD."},
]


def seed():
    if list_products():
        return 0
    for item in SEED:
        create_product({**item, "image": ""})
    return len(SEED)
