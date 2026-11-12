from flask_wtf import FlaskForm
from wtforms import EmailField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Regexp


def _strip(value):
    return value.strip() if isinstance(value, str) else value


CONTACT_TOPICS = [
    ("", "— оберіть тему —"),
    ("cooperation", "Співпраця"),
    ("vacancy", "Пропозиція роботи"),
    ("question", "Запитання"),
    ("other", "Інше"),
]


class ContactForm(FlaskForm):
    name = StringField(
        "Ім'я",
        filters=[_strip],
        validators=[
            DataRequired(message="Вкажіть ім'я."),
            Length(min=4, max=10, message="Ім'я має містити від 4 до 10 символів."),
        ],
    )
    email = EmailField(
        "Email",
        filters=[_strip],
        validators=[
            DataRequired(message="Вкажіть email."),
            Email(message="Введіть коректну адресу електронної пошти."),
            Length(max=120, message="Email не може бути довшим за 120 символів."),
        ],
    )
    phone = StringField(
        "Телефон",
        filters=[_strip],
        validators=[
            DataRequired(message="Вкажіть номер телефону."),
            Regexp(r"^\+380\d{9}$", message="Телефон має бути у форматі +380XXXXXXXXX (9 цифр після +380)."),
        ],
    )
    subject = SelectField(
        "Тема",
        choices=CONTACT_TOPICS,
        validators=[DataRequired(message="Оберіть тему звернення.")],
    )
    message = TextAreaField(
        "Повідомлення",
        filters=[_strip],
        validators=[
            DataRequired(message="Напишіть повідомлення."),
            Length(min=10, max=500, message="Повідомлення має містити від 10 до 500 символів."),
        ],
    )
    submit = SubmitField("Надіслати")
