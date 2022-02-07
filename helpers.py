import os
import json
import requests
import urllib.parse
from binance.client import Client
from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
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

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    try:
        api_key = os.environ.get("api_key")
        api_secret = os.environ.get("api_secret")
        client = Client(api_key, api_secret)
        client.API_URL = 'https://api.binance.com/api'
        quote = client.get_symbol_ticker(symbol=symbol)

    except:
        return None
        
    try:
        return {
            "price": float(quote["price"]),
            "symbol": quote["symbol"],
        }
    except (KeyError, TypeError, ValueError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

def iex_lookup(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"],
        }
    except (KeyError, TypeError, ValueError):
        return None


def get_klines(symbol, start, end):
    api_key = os.environ.get("api_key")
    api_secret = os.environ.get("api_secret")

    client = Client(api_key, api_secret)

    asset = symbol
    start_date = start
    end_date = end
    timeframe = "1d"

    data  = client.get_historical_klines(asset, timeframe, start_date, end_date)

    return data