import os

from flask import render_template, request, redirect, url_for, flash
from flask_security import login_required, current_user
from werkzeug.utils import secure_filename

from models import Post, Tag, User, Comment
from posts.blueprint import PostForm
from app import app, db, allowed_file


@app.route("/")
def home_page():
    return render_template("home_page.html")


@app.route("/blogs")
def blogs():
    search = request.args.get("search")

    page = request.args.get('page')

    if page and page.isdigit() and int(page) > 0:
        page = int(page)
    else:
        page = 1

    if search is not None:
        posts = Post.query.filter(Post.title.contains(search) |
                                  Post.body.contains(search))
        posts = posts.order_by(Post.id.desc())
    else:
        posts = Post.query.order_by(Post.id.desc())

    pages = posts.paginate(page=page, per_page=4)

    return render_template("blogs.html", pages=pages)


@app.route("/blogs/<slug>", methods=["GET", "POST"])
def post_detail(slug):
    post = Post.query.filter(Post.slug==slug).first_or_404()
    if request.method == "POST":
        body = request.form.get("body")
        if body is not None:
            if current_user.is_authenticated:
                try:
                    comment = Comment(body=body)
                    user = (User
                            .query
                            .filter(User.slug==current_user.slug).first())
                    user.comments.append(comment)
                    post.comments.append(comment)
                    db.session.add(comment)
                    db.session.commit()
                except Exception as err:
                    print(err)
            else:
                flash("You are not authenticated")
    return render_template("detail.html", post=post)


@app.route("/users/<slug>", methods=["GET", "POST"])
def user_detail(slug):
    user = User.query.filter(User.slug == slug).first_or_404()
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            user.profile_image = filename
            db.session.commit()

    filename = os.path.join(app.config["UPLOAD_FOLDER"], user.profile_image)
    return render_template("user_detail.html", user=user, filename=filename)


@app.route("/blogs/tag/<name>")
def tag_detail(name):
    tag = Tag.query.filter(Tag.name==name).first_or_404()
    posts = tag.posts.all()
    return render_template("tag_view.html", tag=tag, posts=posts)


@app.route("/blogs/<slug>/edit", methods=["POST", "GET"])
@login_required
def edit_post(slug):
    post = Post.query.filter(Post.slug==slug).first_or_404()

    if request.method == "POST":
        form = PostForm(formdata=request.form, obj=post)
        form.populate_obj(post)
        db.session.commit()

        return redirect(url_for("post_detail", slug=post.slug))

    form = PostForm(obj=post)
    return render_template("edit_post.html", post=post, form=form)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404
