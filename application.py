from cs50 import SQL
import csv
import psycopg2
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
import urllib.request
from functools import wraps

# Configure application
app = Flask(__name__)


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure CS50 Library to use SQLite database
# db = SQL("postgres://zfqpzaclrzlqws:9664716ffbdcaf0c5ee9faced7f00e7bc1309cd8b6c8f9249fe6f58ba1681f57@ec2-54-163-233-89.compute-1.amazonaws.com:5432/dnh0t4rkjhu7r")
db = SQL("sqlite:///finance.db")

def apology(message, code=400):
    """Renders message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


@app.route("/branches")
def branches():
    """Show portfolio of stocks"""
    return render_template("branches.html")


@app.route("/", methods=["GET"])
def Index():
    """Register user"""
    return render_template("Index.html")


@app.route("/climate")
def climate():
    """Show history of transactions"""
    return render_template("climate.html")


@app.route("/energy")
def energy():
    """Show history of transactions"""
    return render_template("energy.html")


@app.route("/solar", methods=["GET", "POST"])
def solar():
    """get user submitted data"""
    return render_template("solar.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
