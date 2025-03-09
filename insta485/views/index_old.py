"""
Insta485 index (main) view.

URLs include:
/accounts/?target=URL
"""
import hashlib
import pathlib
import uuid
import flask
import arrow
from flask import redirect, url_for, session
import insta485


@insta485.app.route('/', methods=['GET'])
def show_index():
    """Render index page."""
    if 'username' not in session:
        return redirect(url_for('show_login'))

    # Connect to database
    connection = insta485.model.get_db()
    # Query database
    logname = session['username']

    cur = connection.execute(
        "SELECT p.postid, p.filename AS pfilename, p.owner, "
        "p.created, u.filename AS ufilename "
        "FROM posts p, users u "
        "WHERE p.owner = u.username AND (p.owner in "
        "(select username2 as owner from following where username1 = ?) "
        "or owner = ?) "
        "order by p.created desc;",
        (logname, logname,)
    )
    data = cur.fetchall()

    for i in data:
        cur = connection.execute(
            "select count(*) from likes where postid = ?;",
            (i['postid'],)
        )
        likes = cur.fetchall()
        i['likes'] = likes[0]['count(*)']

        cur = connection.execute(
            "select owner, text from comments where postid = ?;",
            (i['postid'],)
        )
        comments = cur.fetchall()
        i['comments'] = comments

        cur = connection.execute(
            "select count(*) from likes where postid = ? and owner = ?;",
            (i['postid'], logname,)
        )
        islike = cur.fetchall()
        i['islike'] = islike[0]['count(*)']

        time = i['created']
        time = arrow.get(time)
        time = time.humanize()
        i['created'] = time

    # Add database info to context
    context = {"data": data, "logname": logname}

    return flask.render_template("index.html", **context)


@insta485.app.route('/uploads/<filename>')
def get_img(filename):
    """Return pictures in upload directory."""
    if 'username' not in flask.session:
        flask.abort(403)
    return flask.send_from_directory(
        insta485.app.config['UPLOAD_FOLDER'], filename)


def __account_delete():
    """Delete accounts."""
    if "username" not in flask.session:
        flask.abort(403)
    logname = flask.session['username']
    connection = insta485.model.get_db()
    # Clear portrait
    cur = connection.execute(
        "SELECT filename FROM users WHERE username = ?;",
        (logname,)
    )
    search = cur.fetchall()
    for i in search:
        path = insta485.app.config["UPLOAD_FOLDER"] / i['filename']
        path.unlink()
    # Clear post images
    cur = connection.execute(
        "SELECT filename FROM posts WHERE owner = ?;",
        (logname,)
    )
    search = cur.fetchall()
    for i in search:
        path = insta485.app.config["UPLOAD_FOLDER"] / i['filename']
        path.unlink()
    # Clear database
    connection.execute(
        "DELETE FROM users WHERE username = ?;",
        (flask.session["username"], )
    )
    connection.commit()
    flask.session.pop("username", None)


def __account_edit():
    """Handle account edit."""
    if "username" not in flask.session:
        flask.abort(403)
    logname = flask.session['username']
    fullname = flask.request.form['fullname']
    email = flask.request.form['email']

    if not fullname or not email:
        flask.abort(400)

    connection = insta485.model.get_db()
    connection.execute(
        "UPDATE users SET fullname = ?, "
        "email = ? WHERE username = ?;",
        (fullname, email, logname,)
    )
    connection.commit()

    fileobj = flask.request.files["file"]
    filename = fileobj.filename

    if filename != "":
        # Unpack flask object
        stem = uuid.uuid4().hex
        suffix = pathlib.Path(filename).suffix.lower()
        uuid_basename = f"{stem}{suffix}"
        # Save to disk
        path = insta485.app.config["UPLOAD_FOLDER"] / uuid_basename
        fileobj.save(path)
        file = uuid_basename

        cur = connection.execute(
            "SELECT filename FROM users WHERE username = ?;",
            (flask.session["username"],)
        )
        search = cur.fetchall()
        if search:
            path = insta485.app.config["UPLOAD_FOLDER"] / \
                search[0]['filename']
            path.unlink()
        connection.execute(
            "UPDATE users SET filename = ? "
            "WHERE username = ?;",
            (file, logname, )
        )
        connection.commit()


def __account_create():
    """Handle account create."""
    username = flask.request.form['username']
    # password = flask.request.form['password']
    fullname = flask.request.form['fullname']
    # Unpack flask object
    fileobj = flask.request.files["file"]
    suffix = pathlib.Path(fileobj.filename).suffix.lower()
    uuid_basename = f"{uuid.uuid4().hex}{suffix}"
    # Save to disk
    path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
    fileobj.save(path)
    file = uuid_basename

    if not username or not flask.request.form['password'] or \
            not fullname or not flask.request.form['email'] or not file:
        flask.abort(400)

    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT username FROM users WHERE username = ?;",
        (username,)
    )
    search = cur.fetchall()
    if search:
        flask.abort(409)
    # password storage
    algorithm = 'sha512'
    salt = 'a45ffdcc71884853a2cba9e6bc55e812'
    password_salted = salt + flask.request.form['password']
    hashlib.new(algorithm).update(password_salted.encode('utf-8'))
    password_hash = hashlib.new(algorithm).hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    cur = connection.execute(
        "INSERT INTO users (username, password, "
        "fullname, email, filename) VALUES (?, ?, ?, ?, ?);",
        (username, password_db_string, fullname,
         flask.request.form['email'], file, )
    )
    connection.commit()
    flask.session["username"] = username


def __update_password():
    """Handle updates to the password."""
    if "username" not in flask.session:
        flask.abort(403)
    password = flask.request.form['password']
    new_password1 = flask.request.form['new_password1']
    new_password2 = flask.request.form['new_password2']
    if not password or not new_password1 or not new_password2:
        flask.abort(400)
    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT password FROM users WHERE username = ?;",
        (flask.session["username"],)
    )
    search = cur.fetchall()

    algorithm = 'sha512'
    # salt = uuid.uuid4().hex
    salt = 'a45ffdcc71884853a2cba9e6bc55e812'
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])

    if password_db_string != search[0]['password']:
        flask.abort(403)
    if new_password1 != new_password2:
        flask.abort(401)

    # password storage
    algorithm = 'sha512'
    salt = 'a45ffdcc71884853a2cba9e6bc55e812'
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + new_password1
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    cur = connection.execute(
        "UPDATE users SET password = ? WHERE username = ?;", (
            password_db_string, flask.session["username"],)
    )
    connection.commit()


@insta485.app.route('/accounts/', methods=['POST'])
def accounts():
    """Account Operations."""
    url = flask.request.args.get("target")
    if not url:
        url = "/"
    operation = flask.request.form['operation']
    if operation == "login":
        username = flask.request.form['username']
        password = flask.request.form['password']
        if not username or not password:
            flask.abort(400)
        connection = insta485.model.get_db()
        cur = connection.execute(
            "SELECT password FROM users WHERE username = ?;",
            (username,)
        )
        search = cur.fetchall()
        print(search)
        if len(search) == 0:
            flask.abort(403)
        # password storage
        algorithm = 'sha512'
        salt = 'a45ffdcc71884853a2cba9e6bc55e812'
        hash_obj = hashlib.new(algorithm)
        password_salted = salt + password
        hash_obj.update(password_salted.encode('utf-8'))
        password_hash = hash_obj.hexdigest()
        password_db_string = "$".join([algorithm, salt, password_hash])
        if password_db_string == search[0]['password']:
            flask.session["username"] = username
            return flask.redirect(url)
        flask.abort(403)
    elif operation == "create":
        __account_create()
        return flask.redirect(url)
    elif operation == "delete":
        __account_delete()
        return flask.redirect(url)

    elif operation == "edit_account":
        __account_edit()
        return flask.redirect(url)

    elif operation == "update_password":
        __update_password()
        return flask.redirect(url)
    return None
