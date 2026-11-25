from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, StringField, SubmitField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    Regexp,
    ValidationError,
)

from app import db
from app.users.models import User


def _strip(value):
    return value.strip() if isinstance(value, str) else value


class RegistrationForm(FlaskForm):
    username = StringField(
        "Ім'я користувача",
        filters=[_strip],
        validators=[
            DataRequired(message="Вкажіть ім'я користувача."),
            Length(min=4, max=24, message="Ім'я має містити від 4 до 24 символів."),
            Regexp(
                r"^[A-Za-z][A-Za-z0-9_.-]*$",
                message="Ім'я має починатися з літери й містити лише латинські літери, цифри, крапку, дефіс або підкреслення.",
            ),
        ],
    )
    email = EmailField(
        "Електронна пошта",
        filters=[_strip],
        validators=[
            DataRequired(message="Вкажіть електронну пошту."),
            Email(message="Введіть коректну адресу електронної пошти."),
            Length(max=255, message="Email не може бути довшим за 255 символів."),
        ],
    )
    password = PasswordField(
        "Пароль",
        validators=[
            DataRequired(message="Вкажіть пароль."),
            Length(min=8, message="Пароль має містити щонайменше 8 символів."),
        ],
    )
    confirm_password = PasswordField(
        "Підтвердження пароля",
        validators=[
            DataRequired(message="Підтвердіть пароль."),
            EqualTo("password", message="Паролі мають збігатися."),
        ],
    )
    submit = SubmitField("Зареєструватися")

    def validate_username(self, field):
        user_id = db.session.scalar(
            db.select(User.id).where(User.username == field.data)
        )
        if user_id is not None:
            raise ValidationError("Таке ім'я користувача вже зайняте.")

    def validate_email(self, field):
        user_id = db.session.scalar(
            db.select(User.id).where(db.func.lower(User.email) == field.data.lower())
        )
        if user_id is not None:
            raise ValidationError("Ця електронна пошта вже зареєстрована.")
