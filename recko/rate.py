from flask import (
    Blueprint, g, redirect, render_template, request, url_for
)
import logging
import numpy as np

import tmdbsimple as tmdb

from recko.auth import login_required
from recko.db import get_db
from recko.calc import incr_mean, incr_sum_sq, incr_stdev

bp = Blueprint('rate', __name__, )
tmdb.API_KEY = '9fdda39f0f05f06b359d029706a8a1e0'

logging.basicConfig(level=logging.DEBUG)


@bp.route('/')
def home():

    db = get_db()
    my_movies = []

    user_ratings = (db.execute('SELECT * FROM ratings WHERE user_id = ? ORDER BY rating DESC LIMIT 10', (g.user['id'],))
                    .fetchall())

    for rating in user_ratings:
        my_movie = tmdb.Movies(rating['movie_id']).info()
        my_movie['rating'] = rating['rating']
        my_movie['rating_id'] = rating['id']
        my_movies.append(my_movie)

    valid_ratings = [vr for vr in np.arange(0.5, 5.5, 0.5)]

    return render_template('home.html', my_movies=my_movies, valid_ratings=valid_ratings)


@bp.route('/rate', methods=('POST',))
def rate_movie():
    if request.method == 'POST':

        db = get_db()

        rating_id = request.form['id']
        movie_id = request.form['movie_id']
        user_id = g.user['id']
        rating = request.form['rating']

        movie = db.execute('SELECT * FROM movies WHERE id = ?', (movie_id,)).fetchone()

        # Saved Rating
        if rating_id:

            saved_rating = db.execute('SELECT * FROM ratings WHERE id = ?', (rating_id,)).fetchone()

            # Delete Rating
            if not rating:
                db.execute('DELETE FROM ratings WHERE id = ?', (rating_id,))

                db.execute('UPDATE users SET rating_mean = ?, rating_n = ? WHERE id = ?',
                           (incr_mean(g.user['rating_mean'], g.user['rating_n'], sub_v=saved_rating['rating']),
                            g.user['rating_n'] - 1, user_id))

                new_mean = incr_mean(movie['rating_mean'], movie['rating_n'], sub_v=saved_rating['rating'])
                new_sum_sq = incr_sum_sq(movie['rating_sum_sq'], sub_v=saved_rating['rating'])
                new_stdev = incr_stdev(movie['rating_mean'], new_sum_sq, movie['rating_n'], sub_v=saved_rating['rating'])
                db.execute('UPDATE movies SET rating_mean = ?, rating_stdev = ?, rating_sum_sq = ?, rating_n = ? WHERE id = ?',
                           (new_mean, new_stdev, new_sum_sq, movie['rating_n'] - 1, movie_id))

                db.commit()

            # Update Rating
            else:
                db.execute('UPDATE ratings SET rating = ? WHERE id = ?', (rating, rating_id))

                db.execute('UPDATE users SET rating_mean = ? WHERE id = ?',
                           (incr_mean(g.user['rating_mean'], g.user['rating_n'], add_v=float(rating), sub_v=saved_rating['rating']), user_id))

                new_mean = incr_mean(movie['rating_mean'], movie['rating_n'], add_v=float(rating), sub_v=saved_rating['rating'])
                new_sum_sq = incr_sum_sq(movie['rating_sum_sq'], add_v=float(rating), sub_v=saved_rating['rating'])
                new_stdev = incr_stdev(movie['rating_mean'], new_sum_sq, movie['rating_n'], add_v=float(rating), sub_v=saved_rating['rating'])
                db.execute('UPDATE movies SET rating_mean = ?, rating_stdev = ?, rating_sum_sq = ? WHERE id = ?',
                           (new_mean, new_stdev, new_sum_sq, movie_id))

                db.commit()

        # Add New Rating
        else:
            # Movie not in DB
            if not movie:
                db.execute('INSERT INTO movies (id, rating_mean, rating_stdev, rating_sum_sq, rating_n) VALUES (?,?,?,?,?)',
                           (int(movie_id), float(rating), 0, float(rating) ** 2, 1))
                db.commit()

            # Saved Movie
            else:
                new_mean = incr_mean(movie['rating_mean'], movie['rating_n'], add_v=float(rating))
                new_sum_sq = incr_sum_sq(movie['rating_sum_sq'], add_v=float(rating))
                new_stdev = incr_stdev(movie['rating_mean'], new_mean, movie['rating_stdev'], movie['rating_n'], float(rating))
                db.execute('UPDATE movies SET rating_mean = ?, rating_stdev = ?, rating_sum_sq = ?, rating_n = ? WHERE id = ?',
                           (new_mean, new_stdev, new_sum_sq, movie['rating_n'] + 1, movie_id))

            db.execute('INSERT INTO ratings (user_id, movie_id, rating) VALUES (?,?,?)',
                       (user_id, int(movie_id), float(rating)))

            db.execute('UPDATE users SET rating_mean = ?, rating_n = ? WHERE id = ?',
                       (incr_mean(g.user['rating_mean'], g.user['rating_n'], add_v=float(rating)), g.user['rating_n'] + 1, user_id))

            db.commit()

    return redirect(url_for('rate.home'))
