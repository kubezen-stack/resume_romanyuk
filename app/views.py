from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from werkzeug.exceptions import NotFound

from . import app
from .contact_log import log_contact
from .forms import ContactForm

OWNER_NAME = "Максим Романюк"

RESUME = {
    "role": "DevOps Engineer (Intern / Junior)",
    "about": (
        "Студент інженерії програмного забезпечення з практичним досвідом роботи "
        "з CI/CD-конвеєрами, автоматизацією хмарної інфраструктури та "
        "контейнеризацією (AWS, Docker, Kubernetes, Terraform, Ansible). "
        "Цікавлюся безпекою (сканування коду та залежностей), найкращими практиками "
        "IaC і створенням відтворюваних середовищ. Прагну розвиватися у "
        "професійній DevOps-команді."
    ),
    "education": [
        {
            "title": "Бакалавр, інженерія програмного забезпечення",
            "place": "Карпатський національний університет імені Василя Стефаника",
            "period": "2024 — дотепер",
        },
        {
            "title": "DevOps II Course",
            "place": "SoftServe IT Academy",
            "period": "липень 2025 — вересень 2025",
        },
        {
            "title": "Advanced Practical DevOps",
            "place": "",
            "period": "березень 2026 — травень 2026",
        },
    ],
    "skills": [
        {"group": "Концепції", "tags": ["Linux", "Git", "Мережі", "Scrum"]},
        {"group": "AI-інструменти", "tags": ["Claude", "Gemini", "GitHub Copilot"]},
        {"group": "Мови", "tags": ["Українська (рідна)", "Англійська (B1+)"]},
    ],
    "technologies": [
        {
            "group": "Хмара та інфраструктура",
            "tags": ["AWS (EC2, S3, IAM, CloudWatch, ECS)", "Terraform", "Ansible", "NGINX"],
        },
        {
            "group": "Контейнеризація та оркестрація",
            "tags": ["Docker", "Docker Compose", "Kubernetes"],
        },
        {
            "group": "CI/CD та безпека",
            "tags": ["GitHub Actions", "Jenkins", "SonarCloud", "OWASP Dependency Check", "Trivy"],
        },
        {
            "group": "Розробка",
            "tags": ["Python", "Bash", "JavaScript", "PostgreSQL", "MSSQL"],
        },
        {
            "group": "Моніторинг",
            "tags": ["VictoriaMetrics", "Zabbix", "Grafana", "Loki", "Promtail"],
        },
    ],
    "projects": [
        {
            "title": "Weather Application with Automated CI/CD Pipeline",
            "period": "травень 2025 — січень 2026",
            "points": [
                "Налаштував CI/CD-конвеєр (автоматичний деплой на Render і в Kubernetes).",
                "Контейнеризував застосунок і опублікував образ у Docker Hub.",
                "Додав сканування безпеки: SonarCloud та OWASP.",
            ],
        },
        {
            "title": "AWS Infrastructure Automation",
            "period": "січень 2026",
            "points": [
                "Автоматизував створення інфраструктури AWS (VPC, EC2, S3, DynamoDB).",
                "Написав Ansible-плейбуки для конфігурації серверів.",
                "Додав логування в CloudWatch та зберігання даних у S3.",
            ],
        },
        {
            "title": "SaaS Cost & Optimizer for AWS",
            "period": "лютий 2026 — дотепер",
            "points": [
                "Спроєктував і реалізував інфраструктуру AWS (VPC, EC2, S3, DynamoDB тощо), оптимізовану за вартістю та масштабованістю.",
                "Реалізував автоматичні сповіщення про перевищення бюджету та аномалії витрат.",
            ],
        },
    ],
}

CONTACTS = [
    {"label": "Email", "value": "maksym23102006@gmail.com", "href": "mailto:maksym23102006@gmail.com"},
    {"label": "Телефон", "value": "+380 50 170 34 37", "href": "tel:+380501703437"},
    {"label": "LinkedIn", "value": "linkedin.com/in/maksym-romaniuk-a7a176268",
     "href": "https://www.linkedin.com/in/maksym-romaniuk-a7a176268"},
    {"label": "GitHub", "value": "github.com/kubezen-stack", "href": "https://github.com/kubezen-stack"},
    {"label": "Місто", "value": "Івано-Франківськ, Україна (UTC+2)", "href": ""},
]


@app.context_processor
def inject_globals():
    return {"current_year": datetime.now().year, "owner_name": OWNER_NAME}


@app.route("/")
@app.route("/resume")
def resume():
    return render_template("resume.html", title="Резюме", resume=RESUME)


@app.route("/contacts", methods=["GET", "POST"])
def contacts():
    form = ContactForm()

    if form.validate_on_submit():
        entry = {
            "name": form.name.data,
            "email": form.email.data,
            "phone": form.phone.data,
            "subject": dict(form.subject.choices).get(form.subject.data, form.subject.data),
            "message": form.message.data,
        }
        try:
            log_contact(app.config["CONTACT_LOG_FILE"], entry)
        except OSError:
            app.logger.exception("Не вдалося записати повідомлення з контактної форми")
            flash("Не вдалося зберегти повідомлення. Спробуйте пізніше.", "error")
        else:
            flash(f"Дякуємо, {entry['name']}! Ваше повідомлення надіслано і збережено.", "success")
            return redirect(url_for("contacts"))
    elif request.method == "POST":
        if "csrf_token" in form.errors:
            flash("Сесія форми застаріла або недійсна. Оновіть сторінку й спробуйте ще раз.", "error")
        else:
            flash("Повідомлення не надіслано: виправте помилки у формі.", "error")

    return render_template("contacts.html", title="Контакти", contacts=CONTACTS, form=form)


@app.route("/homepage")
def home():
    agent = request.user_agent
    return render_template("homepage.html", title="Home", agent=agent)

@app.errorhandler(404)
def not_found(error):
    message = error.description if error.description != NotFound.description else None
    return render_template("errors/404.html", title="Не знайдено", message=message), 404
