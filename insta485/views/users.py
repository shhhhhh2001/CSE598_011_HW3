"""
URLs routing for.

/users/*
"""
import flask
from flask import redirect, url_for
import insta485


def get_is_following(username, follower):
    """Check if username is followed by follower."""
    connection = insta485.model.get_db()
    cursor = connection.execute(
        "SELECT * FROM following WHERE username1 = ? AND username2 = ?",
        (username, follower, )
    )
    return cursor.fetchone() is not None


def get_posts_num(username):
    """Get total posts of username."""
    connection = insta485.model.get_db()
    cursor = connection.execute(
        "SELECT postid FROM posts WHERE owner = ?",
        (username,)
    )
    return len(cursor.fetchall())


def get_followers_num(username):
    """Get total followers of username."""
    connection = insta485.model.get_db()
    cursor = connection.execute(
        "SELECT username1 FROM following WHERE username2 = ?",
        (username,)
    )
    return len(cursor.fetchall())


def get_following_num(username):
    """Get total following of username."""
    connection = insta485.model.get_db()
    cursor = connection.execute(
        "SELECT username2 FROM following WHERE username1 = ?",
        (username,)
    )
    return len(cursor.fetchall())


def get_fullname(username):
    """Get fullname of username."""
    connection = insta485.model.get_db()
    cursor = connection.execute(
        "SELECT fullname FROM users WHERE username = ?",
        (username,)
    )
    return cursor.fetchone()['fullname']


def get_posts(username):
    """Get posts of username."""
    connection = insta485.model.get_db()
    cursor = connection.execute(
        "SELECT * FROM posts WHERE owner = ?",
        (username,)
    )
    return cursor.fetchall()


@insta485.app.route('/users/<user_url_slug>/', methods=['GET'])
def show_user(user_url_slug):
    """Render /users/<user_url_slug> page."""
    if not flask.session.get("username"):
        return flask.redirect(flask.url_for('show_login'))
    connection = insta485.model.get_db()
    cursor = connection.execute(
        "SELECT * FROM users WHERE username = ?",
        (user_url_slug,)
    )
    user = cursor.fetchone()
    if user is None:
        flask.abort(404)
    context = {
        'logname': flask.session.get('username'),
        'username': user_url_slug,
        'user_url_slug': user_url_slug,
        'fullname': user['fullname'],
        'is_following': get_is_following(
            flask.session.get('username'), user_url_slug),
        'total_posts_num': get_posts_num(user_url_slug),
        'followers_num': get_followers_num(user_url_slug),
        'following_num': get_following_num(user_url_slug),
        'posts': get_posts(user_url_slug)
    }
    return flask.render_template("users.html", **context)


@insta485.app.route('/users/<user_url_slug>/followers/', methods=['GET'])
def show_user_followers(user_url_slug):
    """Render /users/<user_url_slug>/followers page."""
    if not flask.session.get("username"):
        return flask.redirect(flask.url_for('show_login'))
    logname = flask.session.get('username')
    connection = insta485.model.get_db()
    user = connection.execute(
        "SELECT username,fullname,filename "
        "FROM users "
        "WHERE username = ?;",
        (user_url_slug,)
    ).fetchone()
    if user is None:
        flask.abort(404)
    follow_dict = connection.execute(
        "SELECT username1 AS username2 "
        "FROM following "
        "WHERE username2 = ?;",
        (user_url_slug,)
    ).fetchall()
    login_follow = connection.execute(
        "SELECT username2 "
        "FROM following "
        "WHERE username1 = ?;",
        (logname,)
    ).fetchall()
    for following in follow_dict:
        following["logname_follows_username"] = following in login_follow
        following["filename"] = connection.execute(
            "SELECT filename "
            "FROM users "
            "WHERE username = ?;",
            (following['username2'],)
        ).fetchone()['filename']
    context = {
        "logname": logname,
        "following": follow_dict,
        "username": user_url_slug
    }
    return flask.render_template("followers.html", **context)


@insta485.app.route('/users/<username>/following/', methods=['GET'])
def show_following(username):
    """Render following page."""
    if 'username' not in flask.session:
        return redirect(url_for('show_login'))
    connection = insta485.model.get_db()
    user = connection.execute(
        "SELECT username FROM users WHERE username = ?;",
        (username, )
    ).fetchone()
    if user is None:
        flask.abort(404)

    cur = connection.execute(
        "SELECT username, filename FROM users "
        "WHERE username IN "
        "(SELECT username2 AS username FROM following "
        "WHERE username1 = ?);",
        (username, )
    )
    followings = cur.fetchall()
    logname = flask.session['username']
    for i in followings:
        cur = connection.execute(
            "SELECT username2 FROM following "
            "WHERE username1 = ?;",
            (logname, )
        )
        isfollowing = cur.fetchall()
        if isfollowing is None:
            i['logname_follows_username'] = False
        else:
            i['logname_follows_username'] = True

    context = {"following": followings, "logname": logname,
               "username": username}
    return flask.render_template("following.html", **context)
