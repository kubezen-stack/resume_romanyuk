# Сайт-резюме на Flask (лабораторні роботи 2–6)

## Структура

```
resume_romanyuk/
├── run.py                      # точка входу
├── requirements.txt
├── .env                        # змінні середовища (не в git), шаблон — .env.example
├── instance/                   # SQLite-база data.sqlite (не в git)
├── data/
│   └── products.json           # TinyDB-сховище товарів (створюється автоматично, у .gitignore)
├── app/
│   ├── __init__.py             # create_app(), db, migrate, обробник 404
│   ├── config.py               # Config, DevelopmentConfig, TestingConfig, ProductionConfig
│   ├── views.py                # блюпринт main: резюме, контакти (WTF-форма)
│   ├── forms.py                # ContactForm
│   ├── contact_log.py          # запис контактів у logs/contacts.log
│   ├── templates/              # base, includes, macros/form_macros.html, 404.html
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

| Операція    | Маршрут                           |
| ----------- | --------------------------------- |
| Список      | `GET /product`                    |
| Додавання   | `GET/POST /product/add`           |
| Перегляд    | `GET /product/<int:id>`           |
| Редагування | `GET/POST /product/<int:id>/edit` |
| Видалення   | `POST /product/<int:id>/delete`   |

## Запуск

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
flask run
```

Початкові товари (необов'язково): `flask products seed`

## Тести

```bash
python -m unittest discover -s tests -v
```
