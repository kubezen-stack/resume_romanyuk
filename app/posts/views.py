from flask import flash, redirect, render_template, request, session, url_for

from app import db
from app.users.models import User

from . import post_bp
from .forms import PostForm
from .models import Post


@post_bp.route("/create", methods=["GET", "POST"])
def add_post():
    form = PostForm()

    authors = User.query.all()
    form.author_id.choices = [(author.id, author.username) for author in authors]

    if form.validate_on_submit():
        new_post = Post(
            title=form.title.data,
            content=form.content.data,
            is_active=form.is_active.data,
            posted=form.publish_date.data,
            category=form.category.data,
            user_id=form.author_id.data,
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
    if request.method == "GET":
        form.publish_date.data = post.posted

    if form.validate_on_submit():
        form.populate_obj(post)
        post.posted = form.publish_date.data
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
