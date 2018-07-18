import os
from typing import Dict, List, Any

from flask import Flask, render_template, jsonify, request
import requests

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["GET", "POST"])
def index():
    books = []
    if request.method == "POST":
        book = request.form.get("search")
        books = db.execute("SELECT * FROM books WHERE isbn LIKE :book OR title LIKE :book OR author LIKE :book",
                           {"book": '%'+book+'%'}).fetchall()

    return render_template("index.html", books=books)


@app.route("/books/<string:isbn>")
def book(isbn):
    #Get reviews from api
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": "J59zR3eiKU3tW4UOEvPMw", "isbns": isbn})
    if res.status_code != 200:
        raise Exception("ERROR: API request unsuccessful.")
    data = res.json()

    """List details about a single book."""
    details = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()

    #Check if book exist
    if details is None:
        return render_template("error.html", message="No such book.")

    return render_template("book.html", book=details, rating=data)

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

@app.route("/register")
def register():
    return render_template("registration.html")

@app.route("/login")
def login():
    return render_template("login.html")