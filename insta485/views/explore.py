"""
URLs routing for.

/explore/
"""
import flask
import insta485


@insta485.app.get('/explore/')
def show_explore():
    """Route /explore/."""
    if not flask.session.get("username"):
        return flask.redirect(flask.url_for('login'))
    logname = flask.session.get('username')
    connection = insta485.model.get_db()
    all_user = connection.execute(
        "SELECT username "
        "FROM users "
        "WHERE username != ?;",
        (logname, )
    ).fetchall()
    all_user_list = [e['username'] for e in all_user]
    already_follow = connection.execute(
        "SELECT username2 "
        "FROM following "
        "WHERE username1 = ?;",
        (logname, )
    ).fetchall()
    already_follow_list = [e['username2'] for e in already_follow]
    not_follow = list(set(all_user_list)-set(already_follow_list))
    place_hold = ','.join('?' * len(not_follow))
    not_follow_dict = connection.execute(
        "SELECT username, filename "
        "FROM users "
        f"WHERE username IN ({place_hold}) "
        "ORDER BY username;", not_follow
    ).fetchall()
    context = {
        "logname": logname,
        "not_following": not_follow_dict
    }
    return flask.render_template("explore.html", **context)
