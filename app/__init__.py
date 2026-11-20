import os
from dotenv import load_dotenv
from flask import Flask, render_template
from sqlalchemy import MetaData
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

from .config import config_map

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        "ix": 'ix_%(column_0_label)s',
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    })

db = SQLAlchemy(model_class=Base)
migrate = Migrate()

def create_app(config_name: str = os.environ.get("FLASK_CONFIG", "development")) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    print(f"Running in config: {config_name}")

    db.init_app(app)
    migrate.init_app(app, db)

    from .products import db as products_db
    from .posts import post_bp
    from .products import products_bp
    from .users import users_bp
    from .views import main

    app.register_blueprint(main)
    app.register_blueprint(users_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(post_bp, url_prefix="/post")

    products_db.init_db(app.config["PRODUCTS_DB_FILE"])

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    return app
