import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Book(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    yearvalue = db.Column(db.String, nullable=False)


class Rating(db.Model):
    __tablename__ = "ratings"
    id = db.Column(db.Integer, primary_key=True)
    desc = db.Column(db.String, nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
