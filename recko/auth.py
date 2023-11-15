import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from recko.db import get_db

from datetime import datetime

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=('GET', 'POST'))
def register():

    if request.method == 'POST':

        name = request.form['name']
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        error = None

        if not username:
            error = 'Username is required'
        elif not password:
            error = 'Password is required'
        elif not name:
            name = username

        if error is None:
            try:
                created = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

                db.execute(
                    "INSERT INTO users (name, username, password, created) VALUES (?, ?, ?, ?)",
                    (name, username, generate_password_hash(password), created)
                )
                db.commit()
            except db.IntegrityError:
                error = f"{username} is already registered"
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

        if user is None or not check_password_hash(user['password'], password):
            error = 'Incorrect username or password'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('rate.home'))

        flash(error)

    return render_template('login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('rate.home'))


def login_required(view):

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view()
