from flask import render_template, request, redirect, url_for
from flask_security import login_required

from models import Post, Tag
from posts.blueprint import PostForm
from app import app, db


@app.route("/")
def home_page():
    return render_template("home_page.html")


@app.route("/login")
def login():
    return render_template("login.html")


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


@app.route("/blogs/<slug>")
def post_detail(slug):
    post = Post.query.filter(Post.slug==slug).first_or_404()
    return render_template("detail.html", post=post)


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
