from flask import Flask, render_template
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

from .config import config_map

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
migrate = Migrate()

def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

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
