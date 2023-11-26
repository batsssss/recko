--DROP TABLE IF EXISTS users;
--DROP TABLE IF EXISTS ratings;

--CREATE TABLE users (
    --id INTEGER PRIMARY KEY AUTOINCREMENT,
    --name TEXT NOT NULL,
    --username TEXT UNIQUE NOT NULL,
    --password TEXT NOT NULL,
    --mean_rating INTEGER,
    --created DATETIME
--);

--CREATE TABLE ratings (
    --id INTEGER PRIMARY KEY AUTOINCREMENT,
    --user_id INTEGER NOT NULL,
    --movie_id INTEGER NOT NULL,
    --rating INTEGER NOT NULL,
    --FOREIGN KEY (user_id) REFERENCES users(id)
--);

--CREATE TABLE movies (
    --id INTEGER PRIMARY KEY AUTOINCREMENT,
    --movie_id INTEGER UNIQUE NOT NULL,
    --rating_mean REAL,
    --rating_stdev REAL
--);

--ALTER TABLE users
    --ADD rating_mean REAL;