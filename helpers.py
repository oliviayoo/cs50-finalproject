# Python code for the helper functions for application.py
# Written by Olivia Yoo and Nalani Dziama
# Last updated December 9 2020

# Import necessary functions
import os
import requests
from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    # Sourced from PSET 9 finance helpers.py
    
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


def searchtitle(query):
    """ Search for a movie"""
    
    # Prepares the user's input to be used in the search query
    query = query.replace(" ", "")
    
    # Executes the URL
    url = f"https://imdb-internet-movie-database-unofficial.p.rapidapi.com/search/{query}"

    headers = {
        'x-rapidapi-key': "e520e5912cmsh070e571af3f27afp1d7125jsn51ce21def59c",
        'x-rapidapi-host': "imdb-internet-movie-database-unofficial.p.rapidapi.com"
        }

    response = requests.request("GET", url, headers=headers)
    response.raise_for_status()
    results = response.json()
    results = results.get("titles")
    
    # Returns the list of movies (ID, title, image)
    return results
    

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    # Sourced from PSET 9 finance helpers.py

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def getinfo(movieid):
    """ Return information about the movie """
    
    url = f"https://imdb-internet-movie-database-unofficial.p.rapidapi.com/film/{movieid}"

    headers = {
        'x-rapidapi-key': "e520e5912cmsh070e571af3f27afp1d7125jsn51ce21def59c",
        'x-rapidapi-host': "imdb-internet-movie-database-unofficial.p.rapidapi.com"
        }

    response = requests.request("GET", url, headers=headers)
    response.raise_for_status()
    results = response.json()

    # Gets list of actors
    actors = results.get("cast")
    
    # Stores names of first 5 actors in a list
    actornames = [0] * 5
    for i in range(5):
        actornames[i] = actors[i]['actor']
    
    # Creates a string of all 5 actor names, separated by commas
    actornames = ", ".join(actornames)

    # Create empty dictionary to store info
    movieinfo = {}

    # Fill dictionary with info about the movie
    movieinfo["id"] = results.get("id")
    movieinfo["title"] = results.get("title")
    movieinfo["year"] = results.get("year")
    movieinfo["length"] = results.get("length")
    movieinfo["rating"] = results.get("rating")
    movieinfo["votes"] = results.get("rating_votes")
    movieinfo["image"] = results.get("poster")
    movieinfo["plot"] = results.get("plot")
    movieinfo["trailer"] = results.get("trailer")["link"]
    movieinfo["actors"] = actornames
    
    return movieinfo