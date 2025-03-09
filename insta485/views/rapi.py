"""
URLs routing for.

/following/
/likes/
/comments/
"""
import flask
from flask import request, redirect, url_for
import insta485


@insta485.app.route('/following/', methods=['POST'])
def change_following():
    """Change following state."""
    if 'username' not in flask.session:
        return redirect(url_for('show_login'))
    operation = request.form['operation']
    username = request.form['username']
    logname = flask.session['username']
    target_url = request.args.get('target') if request.args.get(
        'target') else flask.url_for('show_index')
    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT * FROM following WHERE "
        "username1 = ? AND username2 = ?;",
        (logname, username,)
    ).fetchone()

    if operation == "follow":
        if cur is not None:
            flask.abort(409)
        else:
            connection.execute(
                "INSERT INTO following (username1, username2) "
                "VALUES (?, ?);",
                (logname, username, )
            )
    if operation == "unfollow":
        if cur is None:
            flask.abort(409)
        else:
            connection.execute(
                "DELETE FROM following WHERE "
                "(username1, username2)=(?, ?);",
                (logname, username,)
            )

    return redirect(target_url)


@insta485.app.route('/likes/', methods=['POST'])
def change_likes():
    """Change like state."""
    if 'username' not in flask.session:
        return redirect(url_for('show_login'))
    operation = request.form['operation']
    postid = request.form['postid']
    target_url = request.args.get('target') if request.args.get(
        'target') else flask.url_for('show_index')
    connection = insta485.model.get_db()
    logname = flask.session['username']
    cur = connection.execute(
        "SELECT * FROM likes WHERE "
        "owner = ? AND postid = ?;",
        (logname, postid,)
    ).fetchone()
    if operation == "like":
        if cur is not None:
            flask.abort(409)
        else:
            connection.execute(
                "INSERT INTO likes (owner, postid) "
                "VALUES (?, ?);",
                (logname, postid, )
            )
    if operation == "unlike":
        if cur is None:
            flask.abort(409)
        else:
            connection.execute(
                "DELETE FROM likes WHERE "
                "owner = ? AND postid = ?;",
                (logname, postid, )
            )

    return redirect(target_url)


@insta485.app.route('/comments/', methods=['POST'])
def comments_operation():
    """Render /comments page."""
    logname = flask.session.get('username')
    connection = insta485.model.get_db()
    if flask.request.form['operation'] == "create":
        if flask.request.form['text'] == "":
            flask.abort(400)
        else:
            connection.execute(
                "INSERT INTO comments(owner, postid, text) "
                "VALUES (?, ?, ?);",
                (logname,
                 flask.request.form['postid'],
                 flask.request.form['text'], )
            )
            # connection.commit()
    elif flask.request.form['operation'] == "delete":
        test_comment_ownship = connection.execute(
            "SELECT * FROM comments "
            "WHERE commentid = ? AND owner = ? ",
            (flask.request.form['commentid'], logname)
        ).fetchone()
        if not test_comment_ownship:
            flask.abort(403)
        connection.execute(
            "DELETE FROM comments "
            "WHERE commentid = ? ",
            (flask.request.form['commentid'])
        )
    # immediately redirect to URL:
    # If the value of ?target is not set, then redirect to /
    url = flask.request.args.get('target')
    if not url:
        return flask.redirect('/')
    return flask.redirect(url)
