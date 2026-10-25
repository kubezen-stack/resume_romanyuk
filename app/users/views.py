import hmac
from functools import wraps

from flask import flash, redirect, render_template, request, session, url_for
from . import users_bp

VALID_USERS = {"admin": "admin123"}

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
    return render_template("users/profile.html", title="Профіль", username=session["user"])

@users_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    flash("Ви вийшли з системи.", "info")
    return redirect(url_for("users.login"))
