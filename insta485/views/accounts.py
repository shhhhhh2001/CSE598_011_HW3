"""
URLs routing for.

/accounts/*
"""
import flask
import insta485


@insta485.app.route('/accounts/create/', methods=['GET'])
def show_create_account():
    """Routing /accounts/create/."""
    if not flask.session.get('username'):
        return flask.render_template('create_account.html')
    return flask.redirect(flask.url_for('show_edit_account'))


@insta485.app.route('/accounts/password/', methods=['GET'])
def show_password():
    """Routing /accounts/password/."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('show_login'))
    logname = flask.session['username']
    context = {'logname': logname}
    return flask.render_template('password.html', **context)


@insta485.app.route('/accounts/delete/', methods=['GET'])
def show_delete():
    """Render delete page."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('show_login'))
    logname = flask.session['username']
    context = {"logname": logname}
    return flask.render_template("delete.html", **context)


@insta485.app.route('/accounts/logout/', methods=["POST"])
def logout_account():
    """Post /account/logout/."""
    if not flask.session.get("username"):
        return flask.redirect(flask.url_for('show_login'))
    flask.session.pop("username")
    return flask.redirect(flask.url_for('show_login'))


@insta485.app.route('/accounts/edit/', methods=['GET'])
def edit_account():
    """Render /accounts/edit/page."""
    if not flask.session.get("username"):
        return flask.redirect(flask.url_for('login'))
    logname = flask.session.get('username')
    connection = insta485.model.get_db()
    user = connection.execute(
        "SELECT username, fullname, filename, email "
        "FROM users "
        "WHERE username = ?;",
        (logname,)
    ).fetchone()
    context = {
        "logname": logname,
        "username": user['username'],
        "fullname": user['fullname'],
        "user_img_url": user['filename'],
        "email": user['email'],
    }
    return flask.render_template("edit_account.html", **context)


@insta485.app.route('/accounts/login/', methods=['GET'])
def show_login():
    """Render login page."""
    if 'username' not in flask.session:
        return flask.render_template("login.html")
    return flask.redirect(flask.url_for('show_index'))
