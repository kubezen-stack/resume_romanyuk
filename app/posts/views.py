from flask import flash, redirect, render_template, request, url_for

from app import db
from app.users.models import User

from . import post_bp
from .forms import PostForm
from .models import Post, Tag


def set_form_choices(form):
    users = db.session.scalars(db.select(User).order_by(User.id)).all()
    form.author_id.choices = [(u.id, u.username) for u in users]
    tags = db.session.scalars(db.select(Tag).order_by(Tag.id)).all()
    form.tags.choices = [(t.id, t.name) for t in tags]


@post_bp.route("/create", methods=["GET", "POST"])
def add_post():
    form = PostForm()
    set_form_choices(form)

    if form.validate_on_submit():
        new_post = Post(
            title=form.title.data,
            content=form.content.data,
            is_active=form.is_active.data,
            posted=form.publish_date.data,
            category=form.category.data,
            user_id=form.author_id.data,
        )
        new_post.tags = list(
            db.session.scalars(db.select(Tag).where(Tag.id.in_(form.tags.data))).all()
        )
        db.session.add(new_post)
        db.session.commit()
        flash("Post added successfully", "success")
        return redirect(url_for(".get_posts"))  # PRG
    elif request.method == "POST":
        flash("Enter the correct data in the form!", "danger")
    return render_template("add_post.html", form=form, title="Create a New Post")


@post_bp.route("", methods=["GET"], strict_slashes=False)
def get_posts():
    stmt = db.select(Post).where(Post.is_active.is_(True)).order_by(Post.posted.desc())
    posts = db.session.scalars(stmt).all()
    return render_template("all_posts.html", posts=posts, title="Posts")


@post_bp.route("/<int:id>")
def detail_post(id):
    post = db.get_or_404(Post, id)
    return render_template("detail_post.html", post=post, title=post.title)


@post_bp.route("/<int:id>/update", methods=["GET", "POST"])
def edit_post(id):
    post = db.get_or_404(Post, id)

    form = PostForm(obj=post)
    set_form_choices(form)
    if request.method == "GET":
        form.publish_date.data = post.posted
        form.author_id.data = post.user_id
        form.tags.data = [t.id for t in post.tags]

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.is_active = form.is_active.data
        post.category = form.category.data
        post.posted = form.publish_date.data
        post.user_id = form.author_id.data
        post.tags = list(
            db.session.scalars(db.select(Tag).where(Tag.id.in_(form.tags.data))).all()
        )
        db.session.commit()
        flash("Пост оновлено!", "success")
        return redirect(url_for("posts.detail_post", id=post.id))

    return render_template("add_post.html", form=form, title="Редагувати пост")


@post_bp.route("/<int:id>/delete", methods=["GET", "POST"])
def delete_post(id):
    post = db.get_or_404(Post, id)

    if request.method == "POST":
        db.session.delete(post)
        db.session.commit()
        flash("Post deleted successfully", "success")
        return redirect(url_for(".get_posts"))

    return render_template("delete_confirm.html", post=post, title="Delete Post")