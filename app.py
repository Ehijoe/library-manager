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
            form = {}
            # Check if the required fields were given
            for key in ["admission_no", "firstname", 'middlename', 'surname', 'birthdate', 'class']:
                if request.form[key] in ("", None):
                    return "TODO: Error"
                else:
                    form[key] = request.form[key].strip()
            
            # Check if the admission number is a valid number
            try:
                form["admission_no"] = int(form["admission_no"])
                if form["admission_no"] <= 0:
                    raise ValueError
            except ValueError:
                return "TODO: Error"

            # Check if the class is a valid class
            if form["class"] not in CLASSES:
                return "TODO: Error"

            # Check if there is a person with the same name
            cursor.execute("SELECT id FROM people WHERE first_name LIKE ? and surname LIKE ?", (request.form["firstname"], request.form["surname"]))
            person_id = cursor.fetchone()
            if person_id == None:
                # Create a new person
                cursor.execute(
                    """INSERT INTO people (first_name, middle_name, surname, birthdate) VALUES (?, ?, ?, ?)""",
                    (request.form["firstname"], request.form["middlename"], request.form["surname"], request.form["birthdate"]))
                person_id = cursor.lastrowid
            else:
                person_id = person_id["id"]

            # Insert the new student
            cursor.execute("INSERT INTO students (admission_no, person_id, class) VALUES (?, ?, ?)", (form["admission_no"], person_id, form["class"]))
            connection.commit()

            return redirect("/students/add")
        
        if action == "remove":
            search_keys = {}

            # Check which values were used in the search
            for key in request.form:
                if key == "admission_no":
                    try:
                        admission_no = int(request.form[key].strip())
                        if admission_no <= 0:
                            raise ValueError
                    except ValueError:
                        continue
                    search_keys[key] = admission_no
                if request.form.get(key) not in ["", None]:
                    search_keys[key] = request.form.get(key).strip()

            # Ensure there is at least one search key
            if len(search_keys) < 1:
                return "TODO: Error"

            # Generate the query to select relevant students
            beginning = "SELECT * FROM people JOIN students ON people.id=students.person_id WHERE "
            conditions = "class IS NOT 'Retired'"
            for key in search_keys:
                conditions += " AND "
                conditions += key + " LIKE ?"

            # Query the database to get the relevant students
            cursor.execute(beginning + conditions, list(search_keys.values()))
            students = cursor.fetchall()

            return render_template("student_results.html", students=students, action="/students/delete", title="Remove Student")
        
        if action == "delete":
            cursor.execute("UPDATE students SET class = 'Retired' WHERE admission_no = ?", request.form["admission_no"])
            connection.commit()
            return redirect("/")

    # If it is a get request determine which form to show
    if action == "choose":
        return render_template("admin/students.html")
    elif action == "add":
        return render_template("admin/add_student.html", classes=CLASSES)
    elif action == "remove":
        return render_template("student_search.html", classes=CLASSES, title="Remove Student", action="/students/remove")
    else:
        return "TODO: Invalid action"


@app.route("/about")
def about():
    return "TODO!"


if __name__ == "__main__":
    app.run(debug=True)