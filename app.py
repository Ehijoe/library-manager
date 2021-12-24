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
ROLES = {"librarian":"Librarian", "admin":"Administrator"}


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


def is_librarian(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "librarian":
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def index():
    if session.get("role") == "admin":
        return render_template("admin/home.html")
    
    if session.get("role") == "librarian":
        return render_template("librarian/home.html")
    
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
                    (form["firstname"], form["middlename"], form["surname"], request.form["birthdate"]))
                person_id = cursor.lastrowid
            else:
                person_id = person_id["id"]

            # Insert the new student
            cursor.execute(
                """INSERT INTO students (admission_no, person_id, class) VALUES (?, ?, ?) ON CONFLICT(admission_no) DO UPDATE SET class = ?""",
                (form["admission_no"], person_id, form["class"], form["class"]))
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


@app.route("/staff", defaults={"action": "choose"})
@app.route("/staff/<action>", methods=["GET", "POST"])
@is_admin
def staff(action=None):
    # If it is a post request handle check what type it is
    if request.method == "POST":
        # If a staff was added
        if action == "add":
            form = {}
            # Check if the required fields were given
            for key in ["firstname", 'middlename', 'surname', 'birthdate', 'job_title']:
                if request.form[key] in ("", None):
                    return "TODO: Error"
                else:
                    form[key] = request.form[key].strip()

            # Check if there is a person with the same name
            cursor.execute("SELECT id FROM people WHERE first_name LIKE ? and surname LIKE ?", (form["firstname"], form["surname"]))
            person_id = cursor.fetchone()
            if person_id == None:
                # Create a new person
                cursor.execute(
                    """INSERT INTO people (first_name, middle_name, surname, birthdate) VALUES (?, ?, ?, ?)""",
                    (form["firstname"], form["middlename"], form["surname"], form["birthdate"]))
                person_id = cursor.lastrowid
            else:
                person_id = person_id["id"]

            # Insert the new staff
            cursor.execute("SELECT * FROM staff WHERE person_id = ?", str(person_id))
            if cursor.fetchone() != None:
                cursor.execute("UPDATE staff SET job_title = ? WHERE person_id = ?", (form["job_title"], person_id))
            else:
                cursor.execute("""INSERT INTO staff (person_id, job_title) VALUES (?, ?)""", (person_id, form["job_title"]))
            connection.commit()

            return redirect("/staff/add")
        
        if action == "remove":
            search_keys = {}

            # Check which values were used in the search
            for key in request.form:
                if request.form.get(key) not in ["", None]:
                    search_keys[key] = request.form.get(key).strip()

            # Generate the query to select relevant staff
            beginning = "SELECT * FROM people JOIN staff ON people.id=staff.person_id WHERE "
            conditions = "job_title IS NOT 'Retired'"
            for key in search_keys:
                conditions += " AND "
                conditions += key + " LIKE ?"

            # Query the database to get the relevant students
            cursor.execute(beginning + conditions, list(search_keys.values()))
            staff = cursor.fetchall()

            return render_template("staff_results.html", staff=staff, action="/staff/delete", title="Remove Staff")
        
        if action == "delete":
            cursor.execute("UPDATE staff SET job_title = 'Retired' WHERE person_id = ?", request.form["id"])
            connection.commit()
            return redirect("/")

    # If it is a get request determine which form to show
    if action == "choose":
        return render_template("admin/staff.html")
    elif action == "add":
        return render_template("admin/add_staff.html")
    elif action == "remove":
        return render_template("staff_search.html", title="Remove Staff", action="/staff/remove")
    else:
        return "TODO: Invalid action"


@app.route("/users", defaults={"action": "choose"})
@app.route("/users/<action>", methods=["GET", "POST"])
@is_admin
def users(action=None):
    # If it is a post request handle check what type it is
    if request.method == "POST":
        # If a user to be added is searched display the list of possible employees
        if action == "add-list":
            search_keys = {}

            # Check which values were used in the search
            for key in request.form:
                if request.form.get(key) not in ["", None]:
                    search_keys[key] = request.form.get(key).strip()

            # Generate the query to select relevant staff
            beginning = "SELECT * FROM people JOIN staff ON people.id=staff.person_id WHERE "
            conditions = "job_title IS NOT 'Retired'"
            for key in search_keys:
                conditions += " AND "
                conditions += key + " LIKE ?"

            # Query the database to get the relevant students
            cursor.execute(beginning + conditions, list(search_keys.values()))
            staff = cursor.fetchall()

            return render_template("staff_results.html", staff=staff, action="/users/add", title="Add User")

        # If an employee to be added as a user has been selected
        if action == "add":
            user_info = {}
            # Check if the required fields were given
            for key in ["username", "password", "confirmation", "role"]:
                if request.form.get(key) in ("", None):
                    return render_template("admin/add_user.html", id=request.form["id"], roles=ROLES)
                else:
                    user_info[key] = request.form[key].strip()
            
            # Check if the person id is available
            if request.form.get("id") is None:
                return redirect("/users/add")
            else:
                user_info["id"] = request.form.get("id")
            
            # Check if the password matches the confirmation
            if user_info["password"] != user_info["confirmation"]:
                return "TODO"

            # Check if the person is already a user
            cursor.execute("SELECT * FROM users WHERE person_id = ?", user_info["id"])
            if cursor.fetchone():
                return redirect("/")
            
            # Check if the person chose a valid role
            if user_info["role"] not in ROLES:
                return "TODO"

            # Add the user to the database
            password_hash = generate_password_hash(user_info["password"])
            cursor.execute(
                "INSERT INTO users (username, password_hash, user_role, person_id) VALUES (?, ?, ?, ?)",
                (user_info["username"], password_hash, user_info["role"], user_info["id"]))
            connection.commit()

            return redirect("/")
        
        if action == "remove":
            cursor.execute("DELETE FROM users WHERE person_id = ?", request.form.get("id"))
            connection.commit()
            return redirect("/users/remove")
        
        return "TODO"

    # If it is a get request determine which form to show
    if action == "choose":
        return render_template("admin/users.html")
    elif action == "add":
        return render_template("staff_search.html", action="/users/add-list", title="Add User")
    elif action == "remove":
        cursor.execute("SELECT * FROM people JOIN users ON people.id=users.person_id")
        user_list = cursor.fetchall()
        return render_template("admin/user_list.html", users=user_list, title="Delete User", action="/users/remove", roles=ROLES)
    else:
        return "TODO: Invalid action"


@app.route("/reports")
@is_admin
def reports():
    return "TODO"


@app.route("/add_book")
@is_librarian
def add_book():
    return "TODO"


@app.route("/borrow")
@is_librarian
def borrow():
    return "TODO"


@app.route("/return")
@is_librarian
def return_book():
    return "TODO"


@app.route("/damage")
@is_librarian
def damage():
    return "TODO"


@app.route("/about")
def about():
    return "TODO!"


if __name__ == "__main__":
    app.run(debug=True)