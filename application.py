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


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("postgres://zfqpzaclrzlqws:9664716ffbdcaf0c5ee9faced7f00e7bc1309cd8b6c8f9249fe6f58ba1681f57@ec2-54-163-233-89.compute-1.amazonaws.com:5432/dnh0t4rkjhu7r")
# db = SQL("sqlite:///finance.db")

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


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    return render_template("index.html")


@app.route("/home", methods=["GET"])
def home():
    """Register user"""
    return render_template("home.html")


@app.route("/submit", methods=["GET", "POST"])
@login_required
def submit():
    """get user submitted data"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # get values from form
        orientation = request.form.get("orientation")
        WWR = request.form.get("WWR")
        NS_h_shading = request.form.get("NS-h-shading")
        WE_h_shading = request.form.get("WE-h-shading")
        WE_v_shading = request.form.get("WE-v-shading")
        wall_u = request.form.get("wall-u")
        glass_u = request.form.get("glass-u")
        glass_shgc = request.form.get("glass-shgc")
        cooling = request.form.get("cooling")
        heating = request.form.get("heating")
        lighting = request.form.get("lighting")
        DHW = request.form.get("DHW")
        plugload = request.form.get("plugload")

        # ensure form not blank
        if not orientation:
            return apology("missing building orientation", 400)
        if not WWR:
            return apology("missing window to wall ratio", 400)
        if not NS_h_shading:
            return apology("missing NS horizontal shading", 400)
        if not WE_h_shading:
            return apology("missing WE horizontal shading", 400)
        if not WE_v_shading:
            return apology("missing WE verical shading ", 400)
        if not wall_u:
            return apology("missing wall: u-value", 400)
        if not glass_u:
            return apology("missing glass: u-value", 400)
        if not glass_shgc:
            return apology("missing glass: SHGC", 400)
        if not cooling:
            return apology("missing cooling", 400)
        if not heating:
            return apology("missing heating", 400)
        if not lighting:
            return apology("missing lighting", 400)
        if not DHW:
            return apology("missing DHW", 400)
        if not plugload:
            return apology("missing plugload", 400)

        # ensure values is an integer
        orientation = int(orientation)
        WWR = float(WWR)
        NS_h_shading = float(NS_h_shading)
        WE_h_shading = float(WE_h_shading)
        WE_v_shading = float(WE_v_shading)
        wall_u = float(wall_u)
        glass_u = float(glass_u)
        glass_shgc = float(glass_shgc)
        cooling = float(cooling)
        heating = float(heating)
        lighting = float(lighting)
        DHW = float(DHW)
        plugload = float(plugload)
        totals = cooling + heating + lighting + DHW + plugload

        # update energy table
        db.execute("""INSERT INTO energy (user_id, orientation, WWR, NS_h_shading, WE_h_shading, WE_v_shading, wall_u, glass_u, glass_shgc, cooling, heating, lighting, DHW, plugload, total) VALUES(:user_id, :orientation, :WWR, :NS_h_shading, :WE_h_shading, :WE_v_shading, :wall_u, :glass_u, :glass_shgc, :cooling, :heating, :lighting, :DHW, :plugload, :total)""",
                        user_id=session["user_id"], orientation=request.form.get("orientation"), WWR=request.form.get("WWR"), NS_h_shading=request.form.get("NS-h-shading"), WE_h_shading=request.form.get("WE-h-shading"), WE_v_shading=request.form.get("WE-v-shading"), wall_u=request.form.get("wall-u"), glass_u=request.form.get("glass-u"),
                        glass_shgc=request.form.get("glass-shgc"), cooling=request.form.get("cooling"), heating=request.form.get("heating"), lighting=request.form.get("lighting"), DHW=request.form.get("DHW"), plugload=request.form.get("plugload"), total=totals)

        # get user id
        # session["user_id"] = id

        # successful transaction

        # Display portfolio
        flash("Submitted!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("submit.html")


@app.route("/explore")
@login_required
def explore():
    """Show history of transactions"""

    return render_template("explore.html")


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
            return apology("invalid username or password", 403)

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


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # POST
    if request.method == "POST":

        # Validate form submission
        if not request.form.get("username"):
            return apology("missing username")
        elif not request.form.get("password"):
            return apology("missing password")
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match")

        # Add user to database
        id = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",
                        username=request.form.get("username"),
                        hash=generate_password_hash(request.form.get("password")))
        if not id:
            return apology("username taken")

        # Log user in
        session["user_id"] = id

        # Let user know they're registered
        flash("Registered!")
        return redirect("/")

    # GET
    else:
        return render_template("register.html")


@app.route("/download", methods=["GET", "POST"])
@login_required
def download():
    """Download CSV file"""
    if request.method == "POST":
        url = f"http://thsu-thsu.cs50.io:8080/static/cars.csv"
        return urllib.request.urlretrieve(url, "cars.csv")



    else:
        return render_template("download.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
