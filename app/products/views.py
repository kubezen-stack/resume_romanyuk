import os
import uuid
from decimal import Decimal

from flask import abort, current_app, flash, redirect, render_template, request, url_for

from werkzeug.exceptions import RequestEntityTooLarge

from . import db, products_bp
from .forms import DeleteForm, ProductForm


def _static_root():
    return os.path.dirname(current_app.config["PRODUCT_UPLOAD_FOLDER"])


def save_image(file_storage):
    ext = file_storage.filename.rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    folder = current_app.config["PRODUCT_UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    file_storage.save(os.path.join(folder, filename))
    return f"{os.path.basename(folder)}/{filename}"


def delete_image(rel_path):
    if not rel_path:
        return
    folder = os.path.realpath(current_app.config["PRODUCT_UPLOAD_FOLDER"])
    path = os.path.realpath(os.path.join(_static_root(), rel_path))
    if os.path.dirname(path) == folder and os.path.isfile(path):
        os.remove(path)


def category_label(code):
    return dict(current_app.config["PRODUCT_CATEGORIES"]).get(code, code or "—")


@products_bp.context_processor
def helpers():
    def image_url(product):
        from flask import url_for

        rel = product.get("image")
        if rel and os.path.isfile(os.path.join(_static_root(), rel)):
            return url_for("products.static", filename=rel)
        return url_for("products.static", filename="images/no-image.svg")

    return {"image_url": image_url, "category_label": category_label}


def _get_or_404(product_id):
    product = db.get_product(product_id)
    if product is None:
        abort(404, description="Товар не знайдено.")
    return product


@products_bp.route("", strict_slashes=False)
def products():
    return render_template(
        "products/products.html",
        title="Список товарів",
        products=db.list_products(),
        delete_form=DeleteForm(),
    )


@products_bp.route("/<int:product_id>")
def detail_product(product_id):
    product = _get_or_404(product_id)
    return render_template(
        "products/detail_product.html", title=product["name"], product=product, delete_form=DeleteForm()
    )


def _form_to_data(form):
    return {
        "name": form.name.data,
        "content": form.content.data,
        "price": round(float(form.price.data), 2),
        "category": form.category.data,
        "quantity": form.quantity.data,
    }


def _flash_form_errors(form):
    if "csrf_token" in form.errors:
        flash("Сесія форми застаріла або недійсна. Оновіть сторінку й спробуйте ще раз.", "error")
    else:
        flash("Товар не збережено: виправте помилки у формі.", "error")


@products_bp.route("/add", methods=["GET", "POST"])
def add_product():
    form = ProductForm()

    if form.validate_on_submit():
        data = _form_to_data(form)
        data["image"] = save_image(form.image.data) if form.image.data else ""
        product = db.create_product(data)
        flash(f"Товар «{product['name']}» успішно додано.", "success")
        return redirect(url_for("products.detail_product", product_id=product["id"]))
    elif request.method == "POST":
        _flash_form_errors(form)

    return render_template("products/product_form.html", title="Додати товар", form=form, product=None)


@products_bp.route("/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id):
    product = _get_or_404(product_id)
    prefill = {k: v for k, v in product.items() if k != "image"}
    form = ProductForm(data={**prefill, "price": Decimal(str(product["price"]))})

    if form.validate_on_submit():
        data = _form_to_data(form)
        old_image = product.get("image", "")
        if form.image.data:
            data["image"] = save_image(form.image.data)
        db.update_product(product_id, data)
        if form.image.data:
            delete_image(old_image)
        flash(f"Зміни до товару «{data['name']}» збережено.", "success")
        return redirect(url_for("products.detail_product", product_id=product_id))
    elif request.method == "POST":
        _flash_form_errors(form)

    return render_template(
        "products/product_form.html", title=f"Редагувати: {product['name']}", form=form, product=product
    )


@products_bp.route("/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    form = DeleteForm()
    if not form.validate_on_submit():
        flash("Сесія форми застаріла або недійсна. Оновіть сторінку й спробуйте ще раз.", "error")
        return redirect(url_for("products.products"))

    product = db.delete_product(product_id)
    if product is None:
        abort(404, description="Товар не знайдено.")
    delete_image(product.get("image"))
    flash(f"Товар «{product['name']}» видалено.", "success")
    return redirect(url_for("products.products"))


@products_bp.app_errorhandler(RequestEntityTooLarge)
def file_too_large(error):
    flash("Завантажений файл завеликий. Максимальний розмір запиту — "
          f"{current_app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024)} МБ.", "error")
    return redirect(request.referrer or url_for("products.products"))
