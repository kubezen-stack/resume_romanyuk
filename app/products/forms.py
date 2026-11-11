from decimal import Decimal

from flask import current_app
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from werkzeug.datastructures import FileStorage
from wtforms import DecimalField, IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange, ValidationError


def _strip(value):
    return value.strip() if isinstance(value, str) else value

class UaDecimalField(DecimalField):
    def process_formdata(self, valuelist):
        if valuelist:
            valuelist = [valuelist[0].strip().replace(",", ".")]
        try:
            super().process_formdata(valuelist)
        except ValueError:
            raise ValueError("Введіть коректне число.")

class UaIntegerField(IntegerField):
    def process_formdata(self, valuelist):
        try:
            super().process_formdata(valuelist)
        except ValueError:
            raise ValueError("Введіть ціле число.")

def two_decimal_places(form, field):
    if field.data is not None and field.data.as_tuple().exponent < -2:
        raise ValidationError("Ціна може мати не більше двох знаків після коми.")

ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg"]
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8\xff"

def _has_file(field):
    return isinstance(field.data, FileStorage) and bool(field.data.filename)

def image_signature(form, field):
    if not _has_file(field):
        return
    head = field.data.stream.read(8)
    field.data.stream.seek(0)
    if not (head.startswith(PNG_SIGNATURE) or head.startswith(JPEG_SIGNATURE)):
        raise ValidationError("Файл не є коректним зображенням PNG або JPEG.")

def image_size(form, field):
    if not _has_file(field):
        return
    stream = field.data.stream
    stream.seek(0, 2)
    size = stream.tell()
    stream.seek(0)
    limit = current_app.config["MAX_IMAGE_SIZE"]
    if size > limit:
        raise ValidationError(f"Зображення завелике: максимум {limit // (1024 * 1024)} МБ.")

def category_choices():
    return [("", "— оберіть категорію —")] + list(current_app.config["PRODUCT_CATEGORIES"])

class ProductForm(FlaskForm):
    name = StringField(
        "Назва",
        filters=[_strip],
        validators=[
            DataRequired(message="Вкажіть назву товару."),
            Length(min=3, max=100, message="Назва має містити від 3 до 100 символів."),
        ],
    )
    content = TextAreaField(
        "Опис",
        filters=[_strip],
        validators=[
            DataRequired(message="Вкажіть опис товару."),
            Length(max=2000, message="Опис не може бути довшим за 2000 символів."),
        ],
    )
    price = UaDecimalField(
        "Ціна",
        places=2,
        validators=[
            InputRequired(message="Вкажіть ціну."),
            NumberRange(min=Decimal("0.01"), message="Ціна має бути додатною."),
            two_decimal_places,
        ],
    )
    category = SelectField(
        "Категорія",
        validators=[DataRequired(message="Оберіть категорію.")],
    )
    quantity = UaIntegerField(
        "Кількість",
        validators=[
            InputRequired(message="Вкажіть кількість."),
            NumberRange(min=0, message="Кількість не може бути від'ємною."),
        ],
    )
    image = FileField(
        "Зображення",
        validators=[
            FileAllowed(ALLOWED_EXTENSIONS, "Дозволені лише формати PNG, JPG і JPEG."),
            image_signature,
            image_size,
        ],
    )
    submit = SubmitField("Зберегти")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category.choices = category_choices()

class DeleteForm(FlaskForm):
    submit = SubmitField("Видалити")
