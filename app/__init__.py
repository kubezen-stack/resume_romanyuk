from flask import Flask

app = Flask(__name__)
app.config.from_pyfile("../config.py")

from . import views  # noqa: E402,F401
from .users import users_bp  # noqa: E402

app.register_blueprint(users_bp)
