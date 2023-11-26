from flask import (
    Blueprint, redirect, url_for
)

from recko.db import get_db
import csv
import os
from statistics import mean, pstdev

bp = Blueprint('data', __name__)


@bp.route('/import', methods=('GET',))
def import_ratings():
    basedir = os.path.abspath(os.path.dirname(__file__))
    prop_file = os.path.join(basedir, 'static/ratings.csv')

    db = get_db()

    with open(prop_file, newline='', encoding='utf-8') as rf:
        ratings = csv.reader(rf)
        for row in ratings:
            db.execute(
                'INSERT INTO ratings (user_id, movie_id, rating)'
                'VALUES (?, ?, ?)',
                (row[0], row[1], row[2])
            )
            db.commit()

    return redirect(url_for('rate.home'))


@bp.route('/import_movies', methods=('GET',))
def import_movies():
    db = get_db()
    ratings = db.execute('SELECT movie_id, rating FROM ratings ORDER BY movie_id').fetchall()

    cur_movie = 2
    movie_ratings = []
    ratings_len = len(ratings)

    for i, rating in enumerate(ratings):

        if rating['movie_id'] > cur_movie or i + 1 == ratings_len:

            if i + 1 == ratings_len:
                movie_ratings.append(rating['rating'])

            average = mean(movie_ratings)
            stdev = pstdev(movie_ratings)

            try:
                db.execute(
                    'INSERT INTO movies (id, rating_mean, rating_stdev)'
                    'VALUES (?, ?, ?)',
                    (cur_movie, average, stdev)
                )
                db.commit()
            except db.DatabaseError:
                error = db.DatabaseError

            cur_movie = rating['movie_id']
            movie_ratings = []

        movie_ratings.append(rating['rating'])

    return redirect(url_for('rate.home'))


@bp.route('/user_mean', methods=('GET',))
def user_mean():
    db = get_db()
    ratings = db.execute('SELECT user_id, rating FROM ratings ORDER BY user_id').fetchall()

    cur_user = 1
    movie_ratings = []
    ratings_len = len(ratings)

    for i, rating in enumerate(ratings):

        if rating['user_id'] > cur_user or i + 1 == ratings_len:

            if i + 1 == ratings_len:
                movie_ratings.append(rating['rating'])

            average = mean(movie_ratings)

            try:
                db.execute(
                    'UPDATE users SET rating_mean = ?'
                    ' WHERE id = ?',
                    (average, cur_user)
                )
                db.commit()
            except db.DatabaseError:
                error = db.DatabaseError

            cur_user = rating['user_id']
            movie_ratings = []

        movie_ratings.append(rating['rating'])

    return redirect(url_for('rate.home'))


@bp.route('/movie_rating_sq', methods=('GET',))
def movie_rating_sq():
    db = get_db()
    ratings = db.execute('SELECT movie_id, rating FROM ratings ORDER BY movie_id').fetchall()

    cur_movie = 2
    movie_ratings = []
    ratings_len = len(ratings)

    for i, rating in enumerate(ratings):

        if rating['movie_id'] > cur_movie or i + 1 == ratings_len:

            if i + 1 == ratings_len:
                movie_ratings.append(rating['rating'] ** 2)

            sum_sq = sum(movie_ratings)

            try:
                db.execute(
                    'UPDATE movies SET rating_sum_sq = ?'
                    ' WHERE id = ?',
                    (sum_sq, cur_movie)
                )
                db.commit()
            except db.DatabaseError:
                error = db.DatabaseError

            cur_movie = rating['movie_id']
            movie_ratings = []

        movie_ratings.append(rating['rating'] ** 2)

    return redirect(url_for('rate.home'))
