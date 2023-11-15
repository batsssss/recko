import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

import tmdbsimple as tmdb

from recko.auth import login_required
from recko.db import get_db

bp = Blueprint('rate', __name__, )
tmdb.API_KEY = '9fdda39f0f05f06b359d029706a8a1e0'


@bp.route('/')
def home():
    movie = tmdb.Movies(536554)
    response = movie.info()
    return render_template('home.html', title=movie.title)
