# Import external libraries
from sqlite3.dbapi2 import Cursor
from flask import Flask, session, render_template, redirect, request, url_for
import sqlite3
import os
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

# App configuration
app = Flask(__name__)
app.secret_key = b"21#$^7isdg843!^#49dcmge394gn4390" # TODO: store as an environment variable

db = "library.sqlite"

# Global variables
CLASSES = ("Pre Basic 7", "Basic7", "Basic 8", "Basic 9", "SS 1", "SS 2", "SS 3")


# Check if database exists
database_exists = os.path.isfile(db)

# Connect to the database
connection = sqlite3.connect(db, check_same_thread=False)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

# If the database was just created, create the tables.
if database_exists:
    print("Database exists.")
else:
    with open("schema.sql") as schema:
        cursor.executescript(schema.read())


def is_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "admin":
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def index():
    if session.get("role") == "admin":
        return render_template("admin/home.html")
    
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        if request.form.get("username") in [None, ""]:
            return redirect("/login")
        if request.form.get("password") in [None, ""]:
            return redirect("/login")

        # Check if the login is valid
        username = request.form.get("username")
        password = request.form.get("password")
        cursor.execute("SELECT * FROM users WHERE username = ?", [username])
        row = cursor.fetchone()

        # If the user is not registered, return an error
        if row == None:
            return redirect("/login")

        if not check_password_hash(row["password_hash"], password):
            return redirect("/login")

        # Update the user's session
        session["user_id"] = row["id"]
        session["role"] = row["user_role"]

        return redirect("/")
    
    # If it is a get request display the form for login
    return render_template("login.html")


@app.route("/students", defaults={"action": "choose"})
@app.route("/students/<action>", methods=["GET", "POST"])
@is_admin
def students(action=None):
    # If it is a post request handle check what type it is
    if request.method == "POST":
        # If a student was added
        if action == "add":
            # Check if all the fields were given
            for key in ["firstname", 'middlename', 'surname', 'birthdate', 'class']:
                if request.form[key] in ("", None):
                    return "TODO: Error"
            
            # Check if there
            return ""
        
        if action == "remove":
            return "TODO"

    # If it is a get request determine which form to show
    if action == "choose":
        return render_template("admin/students.html")
    elif action == "add":
        return render_template("admin/add_student.html", classes=CLASSES)
    elif action == "remove":
        return "TODO"
    else:
        return "TODO"


@app.route("/about")
def about():
    return "TODO!"


if __name__ == "__main__":
    app.run(debug=True)