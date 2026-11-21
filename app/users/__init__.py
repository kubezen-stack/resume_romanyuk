from flask import Blueprint
from . import models

users_bp = Blueprint(
    "users",
    __name__,
    template_folder="templates",
    url_prefix="/users",
)

from . import views
