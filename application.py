# Python code for running the Miyagi's Movie Machine web application 
# Written by Olivia Yoo and Nalani Dziama
# Last updated December 9 2020

# Import all of the necessary functions
import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

# Get functions from the helpers.py file
from helpers import apology, login_required, searchtitle, getinfo

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

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

# Configure CS50 Library to use SQLite database for this project
db = SQL("sqlite:///miyagis.db")


@app.route("/")
@login_required
def home():
    """ Display home page """
    
    return render_template("home.html")


@app.route("/add", methods=["POST"])
@login_required
def addtolist():
    """Add movie to the user's watchlist and return to the watchlist page"""

    # User reached route via POST
    if request.method == "POST":
        
        # Get information about the movie from the IMDb web database
        movieid = request.form.get("movieid")
        movieinfo = getinfo(movieid)
        movietitle = movieinfo['title']
        movieimage = movieinfo['image']
        movieyear = movieinfo['year']
       
        # Query watchlist SQL database for the movie to determine if the movie needs to be added to the user's watchlist, or if it already exists
        rows = db.execute("SELECT * FROM watchlist WHERE movie_id = ? AND user_id = ? ORDER BY watched", movieid, session["user_id"])

        # Check if movie is already on watchlist
        if len(rows) != 0:
            watchedstatus = rows[0]['watched']
            if watchedstatus == 0:
                flash(movietitle + "(" + movieyear + ") is already on your watchlist!")
                return redirect("/watchlist")
                
            # If movie has already been watched, insert new row with updated number of times watched
            # (eg. watchedtimes = 2 if it's the second time the movie has been added to the watchlist)
            else:
                watchedtimes = db.execute("SELECT watchedtimes FROM watchlist WHERE user_id = ? AND movie_id = ? ORDER BY watchedtimes DESC LIMIT 1", session["user_id"], movieid)
                watchedtimes = int(watchedtimes[0]["watchedtimes"])
                db.execute("INSERT INTO watchlist (user_id, movie_id, image, title, description, watched, watchedtimes, timeadded) VALUES (?,?,?,?,?,?,?,date('now','-5 hours'))", session["user_id"], movieid, movieimage, movietitle, movieyear, 0, watchedtimes+1)
                flash(movietitle + "(" + movieyear + ") has been added to your watchlist!")
                return redirect("/watchlist")
        
        # If movie doesn't already exist, insert into watchlist as the first time watched
        else:
            db.execute("INSERT INTO watchlist (user_id, movie_id, image, title, description, watched, watchedtimes, timeadded) VALUES (?,?,?,?,?,?,?,date('now','-5 hours'))", session["user_id"], movieid, movieimage, movietitle, movieyear, 0, 1)
            flash(movietitle + "(" + movieyear + ") has been added to your watchlist!")
            return redirect("/watchlist")


@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():
    """ Change user's password, return to home page """
    
    # User reached route via POST, submit form
    if request.method == "POST":

        # Check to make sure user completed all fields
        if not request.form.get("currentpassword"):
            return apology("missing current password", 400)
        elif not request.form.get("newpassword"):
            return apology("missing new password", 400)
        elif not request.form.get("confirmation"):
            return apology("missing confirmation password", 400)
        
        # Check to make sure current password is correct
        password = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])
        if not check_password_hash(password[0]["hash"], request.form.get("currentpassword")):
            return apology("incorrect password", 400)
        
        # Check to make sure new password and confirmation match
        elif request.form.get("newpassword") != request.form.get("confirmation"):
            return apology("new passwords don't match", 400)
        
        # Update users database
        newhash = generate_password_hash(request.form.get("newpassword"))
        db.execute("UPDATE users SET hash = ? WHERE id = ?", newhash, session["user_id"])
        
        flash("Password changed!")
        return redirect("/")
    
    # User reached route via GET, display form
    else:
        return render_template("password.html")


@app.route("/info", methods=["POST"])
@login_required
def info():
    """ Display information about a movie """
    
    # Get information about the movie from the IMDb web database
    movieid = request.form.get("movieid")
    movieinfo = getinfo(movieid)

    # Display information page
    return render_template("info.html", movieinfo=movieinfo)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any past user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

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
    
    
@app.route("/random", methods=["GET", "POST"])
@login_required
def random():
    """ Provides random suggestion from top 250 IMDb movies """
    
    # Form has been submitted
    if request.method == "POST":
    
        # Select 1 random movie from table in SQL database with top 250 movies
        movies = db.execute("SELECT * FROM topmovies ORDER BY RANDOM() LIMIT 1")
        
        # Get info about the movie
        movieid = movies[0]["movie_id"]
        movietitle = movies[0]["title"]
        movieimage = movies[0]["image"]
        movierank = movies[0]["rank"]
        movieyear = movies[0]["year"]
        
        # Display results
        return render_template("randomresults.html", movieid=movieid, movietitle=movietitle, movieimage=movieimage,movierank=movierank, movieyear=movieyear)
    
    # Display random movie form
    else:
        return render_template("random.html")
        
    
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)
            
        # Ensure passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match", 400)
        
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Check if username already exists
        if len(rows) == 1:
            return apology("username already exists", 400)
        
        # Insert user into database
        else:
            db.execute("INSERT INTO users (username, hash) VALUES (?,?)", request.form.get("username"), generate_password_hash(request.form.get("password")))
            userid = db.execute("SELECT id FROM users WHERE username = ?", request.form.get("username"))

        # Remember which user has logged in
        session["user_id"] = userid[0]['id']

        # Redirect user to home page
        return redirect("/")
    
    # User reached route via GET (as by clicking a link or via redirect)        
    else:
        return render_template("register.html")
        

@app.route("/remove", methods=["POST"])
@login_required
def remove():
    """ Remove movie from watchlist """
    
    if request.method == "POST":
        
        # Get information about the movie from the IMDb web database
        movieid = request.form.get("movieid")
        movieinfo = getinfo(movieid)
        movietitle = movieinfo['title']
        movieimage = movieinfo['image']
        movieyear = movieinfo['year']
        
        # Remove movie from watchlist
        db.execute("DELETE FROM watchlist WHERE movie_id = ? AND user_id = ? AND watched = ?", request.form.get("movieid"), session["user_id"], 0)
        
        # Flash the name of the movie that's been removed and redirect to watchlist page
        flash(movietitle + "(" + movieyear + ")" + " has been removed from your watchlist.")
        return redirect("/watchlist")
       
        
@app.route("/removehistory", methods=["POST"])
@login_required
def removehistory():
    """ Remove movie from watch history"""
    
    if request.method == "POST":
        
        # Get information about the movie from the IMDb web database
        movieid = request.form.get("movieid")
        movieinfo = getinfo(movieid)
        movietitle = movieinfo['title']
        movieimage = movieinfo['image']
        movieyear = movieinfo['year']

        # Remove movie from watch history
        db.execute("DELETE FROM watchlist WHERE movie_id = ? AND watchedtimes = ? AND user_id = ?", request.form.get("movieid"), request.form.get("watchedtimes"), session["user_id"])
        
        # Flash the name of the movie that's been removed and redirect to watchlist page
        flash(movietitle + "(" + movieyear + ")" + " has been removed from your watch history.")
        return redirect("/watchhistory")

        
@app.route("/review", methods=["GET", "POST"])
@login_required
def review():
    """ Review movie on watchlist """
    
    # If user reaches via POST (as by submitting a form)
    if request.method == "POST":
        
        # Ensure movie title was submitted
        if not request.form.get("movie"):
            return apology("missing movie", 400)
            
        # Ensure review was submitted
        elif not request.form.get("review"):
            return apology("missing review", 400)
        
        # Ensure rating was submitted
        elif not request.form.get("rating"):
            return apology("missing rating", 400)
            
        # Check to make sure rating is between 1 and 10
        userrating = float(request.form.get("rating"))
        if userrating < 1 or userrating > 10:
            return apology("invalid rating", 400)
        
        # Get movie ID from title
        title = request.form.get("movie")
        title = title.replace("\xA0", "")
        results = searchtitle(title)
        movieid = results[0]["id"]
        
        # Get information about the movie from the IMDb web database
        movieinfo = getinfo(movieid)
        movietitle = movieinfo['title']
        movieimage = movieinfo['image']
        movieyear = movieinfo['year']
        
        # Update watchlist table with the review
        db.execute("UPDATE watchlist SET watched = ?, rating = ?, review = ?, timereviewed = date('now','-5 hours') WHERE user_id = ? AND title = ? AND watched = ?", 1, userrating, request.form.get("review"), session["user_id"], movietitle, 0)
        
        # Flash the name of the movie that's been removed and redirect to watch history page where you can see the review
        flash(movietitle + "(" + movieyear + ") has been reviewed!")
        return redirect("/watchhistory")
    
    # If user reaches via GET    
    else:
        
        # Get watchlist from the user
        watchlist = db.execute("SELECT * FROM watchlist WHERE user_id = ? AND watched = 0 ORDER BY title", session["user_id"])
        numbermovies = len(watchlist)
    
        # Display empty page (tells user to add movies) if no movies are on watchlist
        if numbermovies == 0:
            return render_template("emptyreview.html")
        
        # Display form with multiple options of movies to review on watchlist
        else:
            # Create the dropdown menu of movies on the user's watchlist 
            movies = [0] * len(watchlist)
            for i in range(len(watchlist)):
                movies[i] = watchlist[i]['title']
            return render_template("review.html", movies=movies)

        
@app.route("/reviewspecific", methods=["POST"])
@login_required
def reviewspecific():
    """ Review a specific movie """
    
    # Get information about the movie from the IMDb web database
    movieid = request.form.get("movieid")
    movieinfo = getinfo(movieid)
    movietitle = movieinfo['title']
    movieyear = movieinfo['year']
    
    # Display review page specifically for that movie with options only for rating and review
    return render_template("reviewspecific.html", movietitle=movietitle, movieyear=movieyear)
    

@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """ Search for a movie based on title/year"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure search query was submitted
        if not request.form.get("query"):
            return apology("must provide movie title and/or year", 400)

        # Get results by searching IMDb's web database
        query = request.form.get("query")
        results = searchtitle(query)

        # If results are found, redirect to results page
        if len(results) != 0:
            return render_template("searchresults.html", results=results, query=query)
            
        # If not a valid movie title, return apology
        else: 
            return apology("no titles matching your search were found", 400)
        
            
    # User reached route via GET, display form
    else:
        return render_template("search.html")

        
@app.route("/topmovies", methods=["GET"])
@login_required
def topmovies():
    """ Displays top 250 movies on IMDb """
    
    # Get top movies from the SQL database of top 250 movies
    topmovies = db.execute("SELECT * FROM topmovies ORDER BY rank")

    # Display movies
    return render_template("topmovies.html", topmovies=topmovies)


@app.route("/watchhistory", methods=["GET"])
@login_required
def watchhistory():
    """ Displays user's watch history """
    
    # Get watched movies from the user
    movies = db.execute("SELECT * FROM watchlist WHERE user_id = ? AND watched = ?", session["user_id"], 1)
    numbermovies = len(movies)

    # Display empty page if no movies are in the user's watch history
    if numbermovies == 0:
        return render_template("emptywatchhistory.html")
    
    # Otherwise display movies
    else:  
        return render_template("watchhistory.html", movies=movies)


@app.route("/watchlist")
@login_required
def watchlist():
    """Displays user's watchlist"""
    
    # Get watchlist from the user
    watchlist = db.execute("SELECT * FROM watchlist WHERE user_id = ? AND watched = 0 ORDER BY title", session["user_id"])
    numbermovies = len(watchlist)
    
    # Display empty page if no movies are on watchlist
    if numbermovies == 0:
        return render_template("emptywatchlist.html")
    
     # Otherwise display index page
    else:
        return render_template("watchlist.html", watchlist=watchlist)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)