import hmac
import re
from functools import wraps

from flask import flash, make_response, redirect, render_template, request, session, url_for
from . import users_bp

VALID_USERS = {"admin": "admin123"}

COOKIE_KEY_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")
PROTECTED_COOKIES = ("session",)

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            flash("Спочатку увійдіть у систему.", "error")
            return redirect(url_for("users.login"))
        return view(*args, **kwargs)

    return wrapped

@users_bp.route("/hi/<string:name>")
def greetings(name):
    name = name.upper()
    age = request.args.get("age", None, int)

    return render_template("users/hi.html", title="Greeting Page", name=name, age=age)

@users_bp.route("/admin")
def admin():
    to_url = url_for("users.greetings", name="administrator", age=45, _external=True)
    print(to_url)
    return redirect(to_url)

@users_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        expected = VALID_USERS.get(username)
        if expected is not None and hmac.compare_digest(expected, password):
            session["user"] = username
            flash(f"Ласкаво просимо, {username}! Ви успішно увійшли.", "success")
            return redirect(url_for("users.profile"))

        flash("Невірне ім'я користувача або пароль.", "error")
        return redirect(url_for("users.login"))

    if "user" in session:
        return redirect(url_for("users.profile"))
    return render_template("users/login.html", title="Вхід")

@users_bp.route("/profile")
@login_required
def profile():
    return render_template(
        "users/profile.html",
        title="Профіль",
        username=session["user"],
        cookies=request.cookies.items(),
    )


@users_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    flash("Ви вийшли з системи.", "info")
    return redirect(url_for("users.login"))

@users_bp.route("/cookies/add", methods=["POST"])
@login_required
def add_cookie():
    key = request.form.get("key", "").strip()
    value = request.form.get("value", "")
    max_age_raw = request.form.get("max_age", "").strip()

    if not COOKIE_KEY_RE.match(key):
        flash("Ключ кукі: лише латиниця, цифри, '_' та '-' (до 64 символів).", "error")
        return redirect(url_for("users.profile"))
    if key in PROTECTED_COOKIES:
        flash(f"Кукі «{key}» змінювати не можна.", "error")
        return redirect(url_for("users.profile"))

    max_age = None
    if max_age_raw:
        if not max_age_raw.isdigit():
            flash("Термін дії має бути цілим числом секунд.", "error")
            return redirect(url_for("users.profile"))
        max_age = int(max_age_raw)

    response = make_response(redirect(url_for("users.profile")))
    response.set_cookie(key, value, max_age=max_age)
    term = f"{max_age} с" if max_age is not None else "до закриття браузера"
    flash(f"Кукі «{key}» додано (термін дії: {term}).", "success")
    return response


@users_bp.route("/cookies/delete", methods=["POST"])
@login_required
def delete_cookie():
    key = request.form.get("key", "").strip()

    if key in PROTECTED_COOKIES:
        flash(f"Кукі «{key}» видаляти не можна.", "error")
        return redirect(url_for("users.profile"))
    if key not in request.cookies:
        flash(f"Кукі з ключем «{key}» не знайдено.", "warning")
        return redirect(url_for("users.profile"))

    response = make_response(redirect(url_for("users.profile")))
    response.delete_cookie(key)
    flash(f"Кукі «{key}» видалено.", "success")
    return response


@users_bp.route("/cookies/delete-all", methods=["POST"])
@login_required
def delete_all_cookies():
    response = make_response(redirect(url_for("users.profile")))
    removed = 0
    for key in request.cookies:
        if key not in PROTECTED_COOKIES:
            response.delete_cookie(key)
            removed += 1
    flash(f"Видалено кукі: {removed}.", "success" if removed else "warning")
    return response
