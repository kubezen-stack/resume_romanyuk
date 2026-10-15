# Flask-застосунок з Blueprint-ами (лабораторна робота 3)

```
flask_app/
├── app/
│   ├── __init__.py          # створення app, реєстрація blueprint-ів
│   ├── views.py             # маршрути резюме, контакти, /homepage
│   ├── templates/           # base.html, resume.html, contacts.html, homepage.html, includes/
│   ├── static/              # css, images
│   ├── users/               # Blueprint users (префікс /users)
│   └── products/            # Blueprint products (префікс /products)
├── tests/
├── config.py
└── run.py
```

Запуск: `pip install -r requirements.txt && python run.py`
Тести: `python -m unittest discover tests -v`
