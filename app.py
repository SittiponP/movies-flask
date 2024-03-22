
import datetime
import os
from re import I
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from matplotlib.pyplot import title
from numpy import tile
from sqlalchemy import Integer
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
from cs50 import SQL
from helper import apology, login_required


app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Connect Database
db = SQL("sqlite:///movies.db")

currentTime = datetime.datetime.now()


@app.route("/")
@login_required
def index():
    bookings = db.execute(
        "SELECT * FROM booking WHERE userID = ?", session["user_id"])
    movieTitle = db.execute(
        "SELECT movie_name FROM movies JOIN booking ON booking.movie_id = movies.movie_id WHERE userID = ?", session["user_id"])
    name = db.execute(
        "SELECT name, last_name FROM users JOIN booking on booking.userID = users.user_id WHERE userID =?", session["user_id"])

    for booking in bookings:
        booking["bookID"] = bookings[0]["booking_id"]
        booking["quantity"] = bookings[0]["quantity"]
        booking["price"] = bookings[0]["price"]
    return render_template("index.html", name=name, movieTitle=movieTitle, bookings=bookings)


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username", 403)

        elif not request.form.get("password"):
            return apology("must provide username", 403)

        rows = db.execute("SELECT * FROM users WHERE username =?",
                          request.form.get("username"))

        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return apology("must provide username", 403)

        session["user_id"] = rows[0]["user_id"]

        if rows[0]["username"] == "manager":
            return render_template("manager.html")
        else:
            return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()

    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirmation")
        name = request.form.get("name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # check if usernamefield has been fill
        if not username:
            return apology("Must have a username", 400)

        # check if username exit
        elif len(rows) != 0:
            return apology("Username already exit", 400)

        # check if password fullfill
        elif not password:
            return apology("Must provide password", 400)

        # check if confirmation passowrd was fullfill
        elif not confirm:
            return apology("Must provide Confirmation Password", 400)

        elif not name:
            return apology("Must provide name", 400)

        elif not last_name:
            return apology("Must provide last name", 400)

        elif not email:
            return apology("Must provide email", 400)

        # check if confirmation and password are match
        elif not password == confirm:
            return apology("password doesn't match")

        else:
            # Generate password
            hash = generate_password_hash(
                password, method="pbkdf2:sha256", salt_length=8
            )

            # Insert into database
            db.execute(
                "INSERT INTO users (username,password,name,last_name,email) VALUES(?,?,?,?,?)", username, hash, name, last_name, email)

        return render_template("login.html")

    else:
        return render_template("register.html")


@app.route("/movies", methods=["GET", "POST"])
@login_required
def show_movies():
    movies = db.execute("SELECT * FROM movies")

    session["title"] = movies[0]["movie_name"]
    session["genre"] = movies[0]["movie_genre"]
    session["img"] = movies[0]["movie_img"]
    session["movie_id"] = movies[0]["movie_id"]

    return render_template("movies.html", movies=movies)


@app.route("/moviesmanager", methods=["GET", "POST"])
@login_required
def show_moviesmanager():
    movies = db.execute("SELECT * FROM movies")

    return render_template("moviemanager.html", movies=movies)


@app.route("/addmovie", methods=["GET", "POST"])
def addmovie():

    if request.method == "POST":

        movie_name = request.form.get("moviename")
        movie_genre = request.form.get("moviegenre")
        movie_img = request.form.get("movieimg")

        if not movie_name:
            return apology("No Movie Name", 400)

        elif not movie_genre:
            return apology("No movie Genre", 400)

        elif not movie_img:
            return apology("No Movie Image", 400)

        db.execute("INSERT INTO movies(movie_name, movie_genre, movie_img) VALUES(?,?,?)",
                   movie_name,
                   movie_genre,
                   movie_img)

        return render_template("moviemanager.html")

    else:
        return render_template("addmovie.html")


@app.route("/buy", methods=["GET", "POST"])
def buy():
    img = session.get("img")
    title = session.get("title")
    genre = session.get("genre")

    return render_template("buy.html", img=img, title=title, genre=genre)


@app.route("/confirm", methods=["GET", "POST"])
def confirm():
    if request.method == "POST":
        price = int(120)
        quantity = request.form.get("quan")
        img = session.get("img")
        title = session.get("title")
        genre = session.get("genre")
        session["quan"] = quantity

        if not quantity:
            return apology("Input Quantity")
        else:
            total_price = price * int(quantity)
            session["total_price"] = total_price

        return render_template("confirm.html", img=img, title=title, genre=genre, total_price=total_price)

    else:
        return render_template("view.html")


@app.route("/payment", methods=["GET", "POST"])
def payment():

    movie_id = session.get("movie_id")
    quantity = session.get("quan")
    userID = session.get("user_id")
    total_price = session.get("total_price")

    db.execute("INSERT INTO booking(quantity,price,movie_id,userID,date) VALUES(?,?,?,?,?)",
               quantity,
               total_price,
               movie_id,
               userID,
               currentTime
               )

    flash("Successfully")
    return redirect("/")


@app.route("/view", methods=["GET", "POST"])
@login_required
def view():
    bookings = db.execute(
        "SELECT * FROM booking WHERE userID = ?", session["user_id"])
    movieTitle = db.execute(
        "SELECT movie_name FROM movies JOIN booking ON booking.movie_id = movies.movie_id WHERE userID = ?", session["user_id"])
    name = db.execute(
        "SELECT name, last_name FROM users JOIN booking on booking.userID = users.user_id WHERE userID =?", session["user_id"])

    for booking in bookings:
        booking["bookID"] = bookings[0]["booking_id"]
        booking["quantity"] = bookings[0]["quantity"]
        booking["price"] = bookings[0]["price"]
        booking["date"] = bookings[0]["date"]
    return render_template("view.html", name=name, movieTitle=movieTitle, bookings=bookings)


@app.route("/viewall")
@login_required
def viewall():
    bookings = db.execute(
        "SELECT * FROM booking")
    movieTitle = db.execute(
        "SELECT movie_name FROM movies JOIN booking ON booking.movie_id = movies.movie_id")
    name = db.execute(
        "SELECT name, last_name FROM users JOIN booking on booking.userID = users.user_id")

    for booking in bookings:
        booking["bookID"] = bookings[0]["booking_id"]
        booking["quantity"] = bookings[0]["quantity"]
        booking["price"] = bookings[0]["price"]
        booking["date"] = bookings[0]["date"]
    return render_template("view.html", name=name, movieTitle=movieTitle, bookings=bookings)
