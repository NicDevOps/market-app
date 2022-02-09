import os
import datetime
import json
import csv
import talib
# import logging
import pandas as pd
from patterns import patterns
from binance.client import Client
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# app.logger.setLevel(logging.INFO)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
# if not os.environ.get('API_KEY'):
#     raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session.get("user_id")

    shares = db.execute("SELECT symbol, shares_qty, price, total FROM stocks WHERE user_id = ?", user_id)

    if shares:
        for share in shares:
            symbol = share["symbol"]
            quote = lookup(share["symbol"])
            price = quote["price"]
            total_price = share["shares_qty"] * price 
            db.execute("UPDATE stocks SET price = ? WHERE symbol = ?", price, symbol)
            db.execute("UPDATE stocks SET total = ? WHERE symbol = ?", total_price, symbol)

    stocks = db.execute("SELECT symbol, shares_qty, price, total FROM stocks WHERE user_id = ?", user_id)

    if stocks:
        cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
        balance = cash[0]["cash"]
    
        p = stocks[0]["total"]
        total = p + cash[0]["cash"]

        return render_template("index.html", stocks=stocks, balance=balance, total=total)

    else:
        cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
        balance = cash[0]["cash"]
    
        return render_template("cash.html", balance=balance)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("must provide a valid Symbol", 403)

        elif not request.form.get("quantity"):
            return apology("must provide a quantity", 403)

        
        quote = lookup(request.form.get("symbol"))

        if quote == None:
            return apology("Symbol not found", 404)

        p = quote["price"]
        s = quote["symbol"]
        # n = quote["name"]

        symbol = request.form.get("symbol")
        quantity = request.form.get("quantity")

        user_id = session.get("user_id")
       
        cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
        total = p * float(quantity)
        balance = float(cash[0]["cash"]) - total

        if balance >= 0:
            db.execute("UPDATE users SET cash = ? WHERE id = ?", balance, user_id)
        else:
            return apology("Not enough money")

        stocks = db.execute("SELECT * FROM stocks WHERE symbol = ?", symbol)

        if not stocks:
            db.execute("INSERT INTO stocks (user_id, symbol, shares_qty, price, total) VALUES (?, ?, ?, ?, ?)",user_id, symbol, quantity, p, total)
        else:
            shares = db.execute("SELECT shares_qty FROM stocks WHERE user_id = ?", user_id)
            new_quantity = int(quantity) + int(shares[0]["shares_qty"])
            db.execute("UPDATE stocks SET shares_qty = ? WHERE symbol = ?", new_quantity, symbol)

        order_type = 'buy'
        date = datetime.datetime.now()
        db.execute("INSERT INTO orders (user_id, order_type, symbol, shares_num, share_price, total, date) VALUES (?, ?, ?, ?, ?, ?, ?)", user_id, order_type, symbol, quantity, p, total, date)

        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session.get("user_id")
    orders = db.execute("SELECT order_type, symbol, shares_num, share_price, total, date FROM orders WHERE user_id = ?", user_id)
    print(orders)
    return render_template("history.html", orders=orders)


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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

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
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("must provide a valid Symbol", 403)

        quote = lookup(request.form.get("symbol"))
        print(quote)
        if quote == None:
            return apology("Symbol not found", 404)

        # n = quote["name"]
        p = quote["price"]
        s = quote["symbol"]
        # c = quote["change"]

        return render_template("quoted.html", get_price=p, get_symbol=s)

    else:
        return render_template("quote.html")
    # return apology("TODO")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username", 403)

        elif not request.form.get("password"):
            return apology("must provide password", 403)

        if request.form.get("password") != request.form.get("confirm"):
            return apology("Password does not match!", 403)

        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        if len(rows) == 1:
            return apology("username already exist!", 403)
        
        username = request.form.get("username")
        password = request.form.get("password")
        genhash = generate_password_hash(password)
        
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, genhash)

        return render_template("registered.html")
    
    else:
        return render_template("register.html")

    
    # return apology("TODO")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("must provide a valid Symbol", 403)

        elif not request.form.get("quantity"):
            return apology("must provide a quantity", 403)

        quote = lookup(request.form.get("symbol"))

        if quote == None:
            return apology("Symbol not found", 404)

        p = quote["price"]
        s = quote["symbol"]

        symbol = request.form.get("symbol")
        quantity = request.form.get("quantity")

        user_id = session.get("user_id")
       
        cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
        total = p * float(quantity)
        balance = float(cash[0]["cash"]) + total

        shares = db.execute("SELECT shares_qty FROM stocks WHERE user_id = ?", user_id)
        new_quantity = int(shares[0]["shares_qty"]) - int(quantity)

        if new_quantity >= 0:
            db.execute("UPDATE stocks SET shares_qty = ? WHERE symbol = ?", new_quantity, symbol)
            db.execute("UPDATE stocks SET price = ? WHERE symbol = ?", p, symbol)
            db.execute("UPDATE stocks SET total = ? WHERE symbol = ?", total, symbol)
            db.execute("UPDATE users SET cash = ? WHERE id = ?", balance, user_id)
        else:
            return apology("Not enough share", 404)
        
        if new_quantity == 0:
            db.execute("DELETE FROM stocks WHERE symbol = ? AND user_id = ?", symbol, user_id)

        order_type = 'sell'
        date = datetime.datetime.now()
        db.execute("INSERT INTO orders (user_id, order_type, symbol, shares_num, share_price, total, date) VALUES (?, ?, ?, ?, ?, ?, ?)", user_id, order_type, symbol, quantity, p, total, date)

        return redirect("/")

    else:
        return render_template("sell.html")

@app.route("/graph", methods=["GET", "POST"])
@login_required
def graph():

    return render_template("graph.html")


@app.route("/chart", methods=["GET", "POST"])
@login_required
def chart():
    api_key = os.environ.get("API_KEY")
    api_secret = os.environ.get("API_SECRET")
    client = Client(api_key, api_secret)

    candles = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_5MINUTE, "1 day ago UTC")

    processed_candles = []

    for data in candles:
        
        candle = {
            "time": data[0] / 1000, 
            "open": data[1], 
            "high": data[2], 
            "low": data[3], 
            "close": data[4] 
        }

        processed_candles.append(candle)
    # print(processed_candles)
    # return json.dumps(processed_candles)
    return jsonify(processed_candles)


@app.route("/screener", methods=["GET", "POST"])
@login_required
def screen():
    stocks = {}
    with open('data/datasets.csv') as f:
        for row in csv.reader(f):
            stocks[row[0]] = {'Currency' : 'crypto'}
    
    current_pattern = request.args.get('pattern', None)

    if current_pattern:
        pattern_function = getattr(talib, current_pattern)
        datafiles = os.listdir('data/daily_year')
        for filename in datafiles:
            df = pd.read_csv('data/daily_year/{}'.format(filename))

            symbol = filename.split('.')[0]
            
            try:
                result = pattern_function(df['Open'], df['High'], df['Low'], df['Close'])
                last = result.tail(1).values[0]
                # if last != 0:
                #     print('{} triggered {}, results = {}'.format(filename, current_pattern, last))
                if last > 0:
                    stocks[symbol][current_pattern] = 'bullish'
                elif last < 0:
                    stocks[symbol][current_pattern] = 'bearish'
                else:
                    stocks[symbol][current_pattern] = None

            except:
                pass

    return render_template("screener.html", patterns=patterns, stocks=stocks, current_pattern=current_pattern)

@app.route("/snapshot", methods=["GET", "POST"])
@login_required
def snapshot():

    api_key = os.environ.get("api_key")
    api_secret = os.environ.get("api_secret")

    client = Client(api_key, api_secret)

    start="2020.10.1"
    end="2022.23.1"
    timeframe="1d"

    with open("data/datasets.csv") as f:
        companies = f.read().splitlines()
        try:
            for company in companies:
                symbol = company.split(',')[0]
                df = pd.DataFrame(client.get_historical_klines(symbol, timeframe,start,end))
                df=df.iloc[:,:6]
                df.columns=["Date","Open","High","Low","Close","Volume"]
                df=df.set_index("Date")
                df.index=pd.to_datetime(df.index,unit="ms")
                df=df.astype("float")
                df.to_csv('data/daily_year/{}'.format(symbol))
        except:
            pass
    
    return render_template("screener.html")
    
