from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    user_id = session.get("user_id")

    # Query database for cash user has
    rows_users = db.execute("SELECT * FROM users WHERE id = :id", id=user_id)
    cash = rows_users[0]["cash"]

    # Query database for user's portfolio
    rows = db.execute("SELECT * FROM 'index' WHERE user_id = :user_id", user_id=user_id)

    total_total = cash

    # Update database for user's portfolio
    for row in rows:

        shares = row["shares"]
        symbol = row["symbol"]

        # get stock current price from lookup
        lookup_price = lookup(symbol).get("price")
        total = lookup_price * shares
        total_total += total

        # update dictionary price
        row_update = {"price": usd(lookup_price), "total": usd(total)}
        row = row.update(row_update)

    return render_template("index.html", rows=rows, cash=usd(cash), total_total=usd(total_total))


@app.route("/account", methods=["GET", "POST"])
def account():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        user_id = session.get("user_id")

        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        # ensure password not blank
        if not new_password:
            return apology("missing new password", 400)

        # ensure passwords match
        elif not new_password == confirmation:
            return apology("new passwords don't match", 400)

        # hash password
        hash = generate_password_hash(new_password, method="pbkdf2:sha256", salt_length=8)

        # update new password to database
        result = db.execute("UPDATE users SET hash = :hash WHERE id = :user_id",
                            hash=hash, user_id=user_id)

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("account.html")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        user_id = session.get("user_id")

        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # ensure symbol not blank
        if not symbol:
            return apology("missing symbol", 400)

        # ensure shares not blank
        if not shares:
            return apology("missing shares", 400)

        # ensure shares is an integer
        try:
            shares = int(shares)
            if shares < 0:
                return apology("invalid shares", 400)
        except:
            return apology("invalid shares", 400)

        # ensure the stock is valid
        if not lookup(symbol):
            return apology("invalid symbol", 400)

        # get stock values from lookup
        lookup_symbol = lookup(symbol)["symbol"]
        lookup_name = lookup(symbol)["name"]
        lookup_price = float(lookup(symbol)["price"])

        # Query database for cash user has
        rows = db.execute("SELECT * FROM users WHERE id = :id", id=user_id)
        cash = float(rows[0]["cash"])

        # ensure user can afford the shares at current price
        balance = round(cash - lookup_price * shares, 2)
        if balance < 0:
            return apology("can't afford", 400)

        # proceed transaction
        else:

            # update user table
            new_cash = str(balance)
            rows_users = db.execute(
                "UPDATE users SET cash = :cash WHERE id = :id", id=user_id, cash=new_cash)

            # update history table
            rows_history = db.execute("INSERT INTO history (user_id, symbol, name, shares, price) VALUES(:user_id, :symbol, :name, :shares, :price)",
                                      user_id=user_id, symbol=lookup_symbol, name=lookup_name, shares=shares, price=usd(lookup_price))

            # update index table
            rows_index = db.execute("INSERT INTO 'index' (user_id, symbol, name, shares) VALUES(:user_id, :symbol, :name, :shares)",
                                    user_id=user_id, symbol=lookup_symbol, name=lookup_name, shares=shares)
            if not rows_index:
                rows_index = db.execute(
                    "SELECT * FROM 'index' WHERE user_id = :user_id AND name = :name", user_id=user_id, name=lookup_name)
                shares_owned = int(rows_index[0]["shares"])
                rows_index_new = db.execute("UPDATE 'index' SET shares = :shares WHERE user_id = :user_id",
                                            user_id=user_id, shares=shares_owned + shares)

        # successful transaction
        flash("Bought!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Query database for user transaction history
    rows = db.execute("SELECT * FROM history WHERE user_id = :user_id",
                      user_id=session.get("user_id"))

    return render_template("history.html", transactions=rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        symbol = request.form.get("symbol")

        # ensure symbol not blank
        if not symbol:
            return apology("missing symbol", 400)

        # ensure symbol is valid
        if not lookup(symbol):
            return apology("invalid symbol", 400)

        # get stock values from lookup
        lookup_symbol = lookup(symbol)["symbol"]
        lookup_name = lookup(symbol)["name"]
        lookup_price = usd(lookup(symbol)["price"])

        # display stock quote in another templete
        return render_template("/quoted.html", name=lookup_name, symbol=lookup_symbol, price=lookup_price)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # ensure username not blank
        if not username:
            return apology("missing username", 400)

        # ensure password not blank
        elif not password:
            return apology("missing password", 400)

        # ensure passwords match
        elif not password == confirmation:
            return apology("passwords don't match", 400)

        # hash password
        hash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=8)

        # add new user to database
        result = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",
                            username=username, hash=hash)

        # ensure username not exist
        if not result:
            return apology("username taken", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=username)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    user_id = session.get("user_id")

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # ensure symbol not blank
        if not symbol:
            return apology("missing symbol", 400)

        # ensure shares not blank
        if not shares:
            return apology("missing shares", 400)

        # ensure shares is an integer
        try:
            shares = int(shares)
            if shares < 0:
                return apology("invalid shares", 400)
        except:
            return apology("invalid shares", 400)

        # get stock values from lookup
        lookup_symbol = lookup(symbol).get("symbol")
        lookup_name = lookup(symbol).get("name")
        lookup_price = float(lookup(symbol).get("price"))

        # get shares user owned
        rows_index = db.execute(
            "SELECT * FROM 'index' WHERE user_id = :user_id AND name = :name", user_id=user_id, name=lookup_name)
        shares_owned = int(rows_index[0]["shares"])

        # ensure selling within user's shares
        if (shares_owned - shares) < 0:
            return apology("too many shares", 400)

        # proceed transaction
        else:

            # Query database for current cash user has
            rows = db.execute("SELECT * FROM users WHERE id = :id", id=user_id)
            cash = float(rows[0]["cash"])

            # update user table
            new_cash = round(cash + lookup_price * shares, 2)
            rows_users = db.execute(
                "UPDATE users SET cash = :cash WHERE id = :id", id=user_id, cash=new_cash)

            # update history table
            rows_history = db.execute("INSERT INTO history (user_id, symbol, name, shares, price) VALUES(:user_id, :symbol, :name, :shares, :price)",
                                      user_id=user_id, symbol=lookup_symbol, name=lookup_name, shares=-shares, price=usd(lookup_price))

            # update index table
            if (shares_owned - shares) == 0:
                rows_index = db.execute(
                    "DELETE FROM 'index' WHERE user_id = :user_id AND name = :name", user_id=user_id, name=lookup_name)
            else:
                rows_index = db.execute("UPDATE 'index' SET shares = :shares WHERE user_id = :user_id",
                                        user_id=user_id, shares=shares_owned - shares)

        # successful transaction
        flash("Sold!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        rows = db.execute("SELECT symbol FROM 'index' WHERE user_id = :user_id", user_id=user_id)
        return render_template("sell.html", symbols=rows)


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
