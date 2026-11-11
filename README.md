# Сайт-резюме на Flask (лабораторні роботи 2–5)

## Структура

```
resume_romanyuk/
├── run.py                      # точка входу
├── config.py                   # налаштування (SECRET_KEY, TinyDB, upload, категорії)
├── requirements.txt
├── data/
│   └── products.json           # TinyDB-сховище товарів (створюється автоматично, у .gitignore)
├── app/
│   ├── __init__.py             # створення app, реєстрація блюпринтів, init TinyDB
│   ├── views.py                # резюме, контакти (WTF-форма), 404
│   ├── forms.py                # ContactForm
│   ├── contact_log.py          # запис контактів у logs/contacts.log
│   ├── templates/              # base, includes, macros/forms.html, errors/404.html
│   ├── users/                  # блюпринт users
│   └── products/               # блюпринт products (TinyDB + Flask-WTF)
│       ├── __init__.py         # Blueprint, фільтр дати, команда seed
│       ├── db.py               # шар зберігання TinyDB (CRUD)
│       ├── forms.py            # ProductForm, DeleteForm
│       ├── views.py            # маршрути CRUD, робота із зображеннями
│       ├── templates/products/ # список, деталі, форма, модальне вікно видалення
│       └── static/             # images/no-image.svg, uploads/ (завантажені зображення)
└── tests/                      # unittest
```

## Маршрути блюпринта products

| Операція | Маршрут |
|---|---|
| Список | `GET /product` |
| Додавання | `GET/POST /product/add` |
| Перегляд | `GET /product/<int:id>` |
| Редагування | `GET/POST /product/<int:id>/edit` |
| Видалення | `POST /product/<int:id>/delete` |

## Запуск

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Початкові товари (необов'язково): `flask --app run products seed`

## Тести

```bash
python -m unittest discover -s tests -v
```
