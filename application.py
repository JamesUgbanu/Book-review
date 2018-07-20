import os
from typing import Dict, List, Any

from flask import Flask, render_template, jsonify, request, session, flash, abort, redirect, url_for

import requests

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
app.secret_key = 'super secret key'
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["GET", "POST"])
def index():

    if session.get('logged_in'):
        books = []
        record = ""
        if request.method == "POST":
            book = request.form.get("search")
            books = db.execute("SELECT * FROM books WHERE isbn LIKE :book OR title LIKE :book OR author LIKE :book",
                               {"book": '%' + book + '%'}).fetchall()
            if not books:
                record = "No record found"
        return render_template("index.html", books=books, record=record)
    else:
        return render_template('login.html')

@app.route("/books/<string:isbn>")
def book(isbn):
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        #Get reviews from api
        res = requests.get("https://www.goodreads.com/book/review_counts.json",
                           params={"key": "J59zR3eiKU3tW4UOEvPMw", "isbns": isbn})
        if res.status_code != 200:
            raise Exception("ERROR: API request unsuccessful.")
        data = res.json()

        """List details about a single book."""
        details = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()

        #Check if book doesn't exist
        if details is None:
            return render_template("error.html", message="No such book.")

        #Get All comments
        comments = db.execute("SELECT * FROM users JOIN ratings ON ratings.user_id = users.id WHERE book_id = :book_id",
                              {"book_id": details.id}).fetchall()
   
        return render_template("book.html", book=details, rating=data, comments=comments)

@app.route("/api/<string:search_term>")
def book_api(search_term):
    """Return search term."""
    # Make sure book exists.
    books = db.execute("SELECT * FROM books WHERE isbn = :search_term",
                       {"search_term": search_term}).fetchall()
    if not books:
        return jsonify({"error": "Not Found"}), 422
   # Get all books.
    items = []
    for book in books:
        item = {
            "isbn": book.isbn,
            "title": book.title,
            "author": book.author,
            "yearvalue": book.yearvalue
            }

        items.append(item)

    return jsonify(items)
    #return render_template("book.html", books=books)

@app.route("/submit", methods=["POST"])
def submit():

    firstname = request.form.get("firstname")
    lastname = request.form.get("lastname")
    email = request.form.get("email")
    password = request.form.get("password")

    db.execute("INSERT INTO users (firstname, lastname, email, password) VALUES (:firstname, :lastname, :email, :password)",
                       {"firstname": firstname, "lastname": lastname, "email": email, "password": password})
    db.commit()
    return render_template("success.html", firstname=firstname)

@app.route("/register")
def register():
    return render_template("registration.html")

@app.route("/login")
def login():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return redirect(url_for("index"))

@app.route("/check", methods=['POST'])
def check():
    email = request.form.get("email")
    password = request.form.get("password")
    query = db.execute("SELECT * FROM users WHERE email = :email AND password = :password", {"email": email, "password": password}).fetchone()
    if query:
        session['logged_in'] = True
        session['logged_in'] = query.id
    else:
        flash('wrong password!')
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for("index"))

@app.route("/comment", methods=["POST"])
def comment():
    rating_id = request.form.get("rating_id")
    comment = request.form.get("desc")
    book_id = request.form.get("book_id")

    if db.execute("SELECT * FROM ratings WHERE book_id = :book_id AND user_id = :user_id",
                  {"book_id": book_id, "user_id": session['logged_in']}).rowcount > 0:
        flash('Whoops!! You already rated this book!')
    else:
        db.execute("INSERT INTO ratings(comment, book_id, user_id, rating) VALUES (:comment, :book_id, :user_id, :rating)",
               {"comment": comment, "book_id" : book_id, "user_id": session['logged_in'], "rating": rating_id})
        db.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run()