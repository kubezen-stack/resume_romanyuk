# Сайт-резюме на Flask (лабораторна робота 2)

## Структура

```
resume_site/
├── app.py                  # Flask-застосунок і маршрути
├── requirements.txt
├── templates/
│   ├── base.html           # базовий шаблон (заголовок, меню, контент, футер)
│   ├── resume.html         # наслідує base.html
│   ├── contacts.html       # наслідує base.html
│   └── includes/
│       ├── nav.html        # навігаційне меню (include)
│       └── footer.html     # футер (include)
└── static/
    ├── css/styles.css      # власні стилі поверх Bootstrap
    └── images/avatar.svg   # зображення на сторінці резюме
```

## Запуск

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Відкрийте http://127.0.0.1:5000
