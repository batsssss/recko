from flask import (
    Blueprint, redirect, url_for, g, request
)

import csv
import os
from statistics import mean, pstdev
from heapq import heapify, heappop
import json

from recko.db import get_db
from recko.calc import adj_cos_sim, predict_rating

bp = Blueprint('data', __name__)


# Build Similarity Matrix
@bp.route('/build_sim_mx', methods=('GET',))
def build_sim_mx():

    start = int(request.args.get('start'))
    end = int(request.args.get('end'))

    if not start or not end:
        return redirect(url_for('rate.home'))

    db = get_db()
    movies = db.execute('SELECT * FROM movies ORDER BY id').fetchall()
    len_movies = len(movies)

    basedir = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(basedir, 'static/sims_mx.json'), 'r') as f:
        sims_mx = json.load(f)

    top_k_neighbours = 30
    sim_score_threshold = 0.5

    sims = {}

    rating_sql = ('SELECT r.movie_id, r.rating, r.user_id, u.rating_mean '
                  'FROM ratings r JOIN users u ON r.user_id = u.id '
                  'WHERE movie_id = ?')

    for i in range(start - 1, end):

        i_id = movies[i]['id']
        ratings_i = db.execute(rating_sql, (i_id,)).fetchall()

        u_ratings_i = {}
        for ri in ratings_i:
            u_ratings_i[ri['user_id']] = dict(ri)

        for j in range(0, len_movies):

            if i == j or (str(i) in sims_mx and str(j) in sims_mx[str(i)]):
                continue

            j_id = movies[j]['id']

            ratings_j = db.execute(rating_sql, (j_id,)).fetchall()
            u_ratings_j = {}

            for ri in ratings_j:
                u_ratings_j[ri['user_id']] = dict(ri)

            ratings_ix = dict_ix(u_ratings_i, u_ratings_j)

            if len(ratings_ix) > 0:
                sim = adj_cos_sim(ratings_ix)

                if sim >= sim_score_threshold:
                    neg_sim = -sim

                    if i_id in sims:
                        sims[i_id].append((neg_sim, j_id))
                    else:
                        sims[i_id] = [(neg_sim, j_id)]

                    if j_id in sims:
                        sims[j_id].append((neg_sim, i_id))
                    else:
                        sims[j_id] = [(neg_sim, i_id)]

    for i_id in sims:
        if str(i_id) in sims_mx:
            for sim_id in sims_mx[str(i_id)]:
                sims[i_id].append((-(sims_mx[str(i_id)][sim_id]), int(sim_id)))
            del sims_mx[str(i_id)]

    for i_id in sims:

        heapify(sims[i_id])

        k_counter = 0
        while sims[i_id] and k_counter < top_k_neighbours:

            sim_tpl = heappop(sims[i_id])
            sim_score = -sim_tpl[0]

            if i_id in sims_mx:
                sims_mx[i_id][sim_tpl[1]] = sim_score
            else:
                sims_mx[i_id] = {sim_tpl[1]: sim_score}

            k_counter += 1

    with open(os.path.join(basedir, 'static/sims_mx.json'), 'w') as f:
        json.dump(sims_mx, f, indent=1)

    return redirect(url_for('rate.home'))


# Recommend Movies
def recommend(k):
    db = get_db()
    basedir = os.path.abspath(os.path.dirname(__file__))
    sims_mx_path = os.path.join(basedir, 'static/sims_mx.json')

    ratings = db.execute(
        'SELECT movie_id, rating, rating_mean, rating_stdev '
        'FROM ratings r JOIN movies m ON m.id = r.movie_id '
        'WHERE user_id = ?',
        (g.user['id'],)).fetchall()

    with open(sims_mx_path, 'r') as f:
        sims_mx = json.load(f)

    rated = {}

    for rating in ratings:
        if str(rating['movie_id']) in sims_mx:
            rated[rating['movie_id']] = {
                'sims': sims_mx[str(rating['movie_id'])],
                'rating_j': rating['rating'],
                'mean_j': rating['rating_mean'],
                'stdev_j': rating['rating_stdev']
            }

    sims = {}
    for rated_movie_id in rated:
        for sim_movie_id in rated[rated_movie_id]['sims']:

            if int(sim_movie_id) in rated:
                continue

            rated_movie_data = {
                'sim_ij': rated[rated_movie_id]['sims'][sim_movie_id],
                'rating_j': rated[rated_movie_id]['rating_j'],
                'mean_j': rated[rated_movie_id]['mean_j'],
                'stdev_j': rated[rated_movie_id]['stdev_j']
            }
            if sim_movie_id in sims:
                sims[sim_movie_id]['sims'][rated_movie_id] = rated_movie_data
            else:
                sim_movie = db.execute('SELECT rating_mean, rating_stdev, title, year, poster_path '
                                       'FROM movies '
                                       'WHERE id = ?',
                                       (sim_movie_id,)).fetchone()
                sims[sim_movie_id] = {
                    'id': sim_movie_id,
                    'sims': {rated_movie_id: rated_movie_data},
                    'mean_i': sim_movie['rating_mean'],
                    'stdev_i': sim_movie['rating_stdev'],
                    'title': sim_movie['title'],
                    'year': sim_movie['year'],
                    'poster_path': sim_movie['poster_path']
                }
    predicted_ratings = []
    for sim in sims:
        predicted_ratings.append((-predict_rating(sims[sim]), sims[sim]))

    heapify(predicted_ratings)

    reckos = []
    max_reckos = k
    r_counter = 0
    while predicted_ratings and r_counter < max_reckos:
        recko = heappop(predicted_ratings)
        reckos.append({
            'id': recko[1]['id'],
            'title': recko[1]['title'],
            'year': recko[1]['year'],
            'poster_path': recko[1]['poster_path'],
            'rating_pr': -recko[0]
        })
        r_counter += 1

    return reckos


# Dictionary Intersection
# https://www.geeksforgeeks.org/python-intersect-two-dictionaries-through-keys/
def dict_ix(dict_1, dict_2):
    return {x: dict_1[x] | {'movie_id_j': dict_2[x]['movie_id'], 'rating_j': dict_2[x]['rating']} for x in dict_1 if
            x in dict_2}


# Importing and Alteration of Data
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
