from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateTimeLocalField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length

from app.users.models import User

CATEGORIES = [
    ("news", "News"),
    ("publication", "Publication"),
    ("tech", "Tech"),
    ("other", "Other"),
]


class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=2)])
    content = TextAreaField(
        "Content", render_kw={"rows": 5, "cols": 40}, validators=[DataRequired()]
    )
    is_active = BooleanField("Active Post")
    publish_date = DateTimeLocalField(
        "Publish Date", format="%Y-%m-%dT%H:%M", default=datetime.now
    )
    category = SelectField("Category", choices=CATEGORIES, validators=[DataRequired()])
    author_id = SelectField("Author", coerce=int, validators=[DataRequired()])
    tags = SelectMultipleField("Tags", coerce=int)
    submit = SubmitField("Add Post")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.author_id.choices = [(a.id, a.username) for a in User.query.order_by(User.id)]
