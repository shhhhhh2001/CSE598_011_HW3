"""
URLs routing for.

/posts/
"""
import os
import uuid
import pathlib
import flask
import arrow
import insta485


def get_post_owner(postid_url_slug):
    """Return the username of the owner of the post."""
    connection = insta485.model.get_db()
    cursor = connection.execute(
        "SELECT owner FROM posts WHERE postid = ?",
        (postid_url_slug,)
    )
    return cursor.fetchone()["owner"]


def get_owner_img_url(owner):
    """Return the img_url of the owner of the post."""
    connection = insta485.model.get_db()
    cursor = connection.execute(
        "SELECT filename FROM users WHERE username = ?",
        (owner,)
    )
    return cursor.fetchone()["filename"]


def get_timestamp(postid_url_slug):
    """Return the timestamp of the post."""
    connection = insta485.model.get_db()
    cursor = connection.execute(
        "SELECT created FROM posts WHERE postid = ?",
        (postid_url_slug,)
    )
    return arrow.get(cursor.fetchone()["created"]).humanize()


def get_img_url(postid_url_slug):
    """Return the img_url of the post."""
    connection = insta485.model.get_db()
    cursor = connection.execute(
        "SELECT filename FROM posts WHERE postid = ?",
        (postid_url_slug,)
    )
    return cursor.fetchone()["filename"]


def get_likes(postid_url_slug):
    """Return the number of likes of the post."""
    connection = insta485.model.get_db()
    cursor = connection.execute(
        "SELECT likeid FROM likes WHERE postid = ?",
        (postid_url_slug,)
    )
    return len(cursor.fetchall())


def get_comments(postid_url_slug):
    """Return comments of the post."""
    connection = insta485.model.get_db()
    cursor = connection.execute(
        "SELECT * FROM comments WHERE postid = ?",
        (postid_url_slug,)
    )
    return cursor.fetchall()


def get_iflike(postid_url_slug):
    """Return if the post is liked by the user."""
    connection = insta485.model.get_db()
    cursor = connection.execute(
        "SELECT * FROM likes WHERE postid = ? AND owner = ?",
        (postid_url_slug, flask.session.get("username"), )
    )
    return cursor.fetchone() is not None


@insta485.app.route("/posts/<postid_url_slug>/", methods=["GET"])
def show_post(postid_url_slug):
    """Render /posts/<post_url_slug>/ page."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('show_login'))
    connection = insta485.model.get_db()
    cursor = connection.execute(
        "SELECT * FROM posts WHERE postid = ?",
        (postid_url_slug,)
    )
    post = cursor.fetchone()
    if not post:
        flask.abort(404)
    else:
        context = {
            "post": post,
            "postid": postid_url_slug,
            "logname": flask.session.get("username"),
            "owner": get_post_owner(postid_url_slug),
            "owner_img_url": get_owner_img_url(
                get_post_owner(postid_url_slug)),
            "timestamp": get_timestamp(postid_url_slug),
            "img_url": get_img_url(postid_url_slug),
            "likes": get_likes(postid_url_slug),
            "comments": get_comments(postid_url_slug),
            "iflike": get_iflike(postid_url_slug)
        }
    return flask.render_template("posts.html", **context)


@insta485.app.post('/posts/')
def post_opt():
    """Handle posts related operations."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('show_login'))
    target = flask.request.args.get('target')
    operation = flask.request.form.get('operation')
    logname = flask.session['username']
    connection = insta485.model.get_db()
    if operation == 'create':
        if not flask.request.files.get('file'):
            flask.abort(400)
        else:
            # Unpack flask object
            fileobj = flask.request.files["file"]
            filename = fileobj.filename
            stem = uuid.uuid4().hex
            suffix = pathlib.Path(filename).suffix.lower()
            uuid_basename = f"{stem}{suffix}"
            # Save to disk
            path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
            fileobj.save(path)

            connection.execute(
                "INSERT INTO posts (filename, owner) "
                "VALUES (?, ?)",
                (uuid_basename, logname, )
            )
    elif operation == "delete":
        postid = flask.request.form.get('postid')
        item = connection.execute(
            "SELECT * FROM posts "
            "WHERE postid = ?",
            (postid, )
        ).fetchone()
        if not item:
            flask.abort(403)
        uid_name = connection.execute(
            "SELECT * FROM posts WHERE postid = ?",
            (postid, )
        ).fetchone().get('filename')
        os.remove(os.path.join(insta485.app.config['UPLOAD_FOLDER'], uid_name))
        connection.execute(
            "DELETE FROM posts WHERE postid = ?",
            (postid, )
        )
    if target:
        return flask.redirect(target)
    return flask.redirect(f'/users/{logname}/')
