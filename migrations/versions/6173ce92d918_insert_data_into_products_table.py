"""Insert data into products table

Revision ID: 6173ce92d918
Revises: 8619f76517db
Create Date: 2026-11-20 13:43:11.640969

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, column


# revision identifiers, used by Alembic.
revision = '6173ce92d918'
down_revision = '8619f76517db'
branch_labels = None
depends_on = None


def upgrade():
    # --- Описи таблиць для bulk_insert ---
    categories_table = sa.table('categories', column('id', sa.Integer), column('name', sa.String))

    products_table = table('products',
        column('name', sa.String),
        column('price', sa.Float),
        column('active', sa.Boolean),
        column('category_id', sa.Integer),
    )

    # --- Вставка категорій ---
    op.bulk_insert(categories_table, [
        {'name': 'Electronics'},
        {'name': 'Books'},
        {'name': 'Clothing'},
    ])

    # --- Вставка продуктів ---
    op.bulk_insert(products_table, [
        {'name': 'Laptop', 'price': 1200.0, 'active': True, 'category_id': 1},
        {'name': 'Smartphone LG', 'price': 800.0, 'active': True, 'category_id': 1},
        {'name': 'Novel', 'price': 20.0, 'active': True, 'category_id': 2},
        {'name': 'T-Shirt', 'price': 25.0, 'active': False, 'category_id': 3},
    ])

def downgrade():
   # Видаляємо тільки ці вставлені продукти та категорії

   # Видаляємо продукти по назвах
    op.execute("""
        DELETE FROM products
        WHERE name IN ('Ultrabook', 'Laptop', 'Smartphone LG', 'Novel', 'T-Shirt');
    """)

    # Видаляємо категорії по назвах
    op.execute("""
        DELETE FROM categories
        WHERE name IN ('Electronics', 'Books', 'Clothing');
    """)
