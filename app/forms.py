from flask_wtf import FlaskForm
from wtforms import EmailField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length


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
            Length(min=2, max=50, message="Ім'я має містити від 2 до 50 символів."),
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
    topic = SelectField(
        "Тема",
        choices=CONTACT_TOPICS,
        validators=[DataRequired(message="Оберіть тему звернення.")],
    )
    message = TextAreaField(
        "Повідомлення",
        filters=[_strip],
        validators=[
            DataRequired(message="Напишіть повідомлення."),
            Length(min=10, max=1000, message="Повідомлення має містити від 10 до 1000 символів."),
        ],
    )
    submit = SubmitField("Надіслати")
