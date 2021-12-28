# Import external libraries
import re
from sqlite3.dbapi2 import Cursor
from flask import Flask, session, render_template, redirect, request, url_for, flash
import sqlite3
import os
from flask.templating import Environment
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from datetime import date, timedelta

# App configuration
app = Flask(__name__)
app.secret_key = b"21#$^7isdg843!^#49dcmge394gn4390" # TODO: store as an environment variable

db = "library.sqlite"

# Global variables
CLASSES = ("Pre Basic 7", "Basic 7", "Basic 8", "Basic 9", "SS 1", "SS 2", "SS 3")
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
        print("Database Created")
        # Test Users
        cursor.execute("INSERT INTO people (id, first_name, surname) VALUES (1, 'test', 'user')")
        cursor.execute(
            "INSERT INTO users (username, password_hash, user_role, person_id) VALUES ('admin', ?, 'admin', 1)",
            [generate_password_hash("test")])
        cursor.execute(
            "INSERT INTO users (username, password_hash, user_role, person_id) VALUES ('librarian', ?, 'librarian', 1)",
            [generate_password_hash("test")])
        connection.commit()
        print("Test users made")


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


def get_unreturned(title, action):
    "Returns a rendered template with a list of unreturned books"
    # Get the borrow information for students
    query = """SELECT admission_no,
            first_name,
            middle_name,
            surname,
            class,
            title,
            author,
            date_expected,
            borrow_id
            FROM borrows
            JOIN people ON borrows.person_id = people.id
            JOIN students ON borrows.person_id = students.person_id
            JOIN books ON borrows.book_id = books.id
            JOIN unreturned ON borrows.id = unreturned.borrow_id"""
    cursor.execute(query)
    student_borrows = cursor.fetchall()

    # Get the borrow information for staff
    query = """SELECT first_name,
            middle_name,
            surname,
            job_title,
            title,
            author,
            date_expected,
            borrow_id
            FROM borrows
            JOIN people ON borrows.person_id = people.id
            JOIN staff ON borrows.person_id = staff.person_id
            JOIN books ON borrows.book_id = books.id
            JOIN unreturned ON borrows.id = unreturned.borrow_id"""
    cursor.execute(query)
    staff_borrows = cursor.fetchall()

    return render_template(
        "unreturned.html",
        title=title,
        student_borrows=student_borrows,
        staff_borrows=staff_borrows,
        action=action)


@app.context_processor
def my_utility_processor():

    def get_url(*args, **kwargs):
        try:
            return url_for(*args, **kwargs)
        except:
            return None
    
    return dict(get_url=get_url)


@app.template_filter("heading_filter")
def heading_filter(heading: str) -> str:
    "A filter that formats headings by replacing underscores with spaces and capitalizing every word."
    words = heading.split("_")
    words = [word.capitalize() for word in words]
    return " ".join(words)


@app.route("/")
def index():
    if session.get("role") == "admin":
        return render_template("admin/home.html")
    
    if session.get("role") == "librarian":
        return render_template("librarian/home.html")
    
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.pop("user_id", None)
    session.pop("role", None)

    if request.method == "POST":
        if request.form.get("username") in [None, ""]:
            flash("You must enter a username", "danger")
            return redirect("/login")
        if request.form.get("password") in [None, ""]:
            flash("You must enter a password!", "danger")
            return redirect("/login")

        # Check if the login is valid
        username = request.form.get("username")
        password = request.form.get("password")
        cursor.execute("SELECT * FROM users WHERE username = ?", [username])
        row = cursor.fetchone()

        # If the user is not registered, return an error
        if row == None:
            flash("Invalid Username or Password!", "danger")
            return redirect("/login")

        if not check_password_hash(row["password_hash"], password):
            flash("Invalid Username or Password!", "danger")
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
                    flash("You must fill all fields!", "warning")
                    return redirect("/students/add")
                else:
                    form[key] = request.form[key].strip()
            
            # Check if the admission number is a valid number
            try:
                form["admission_no"] = int(form["admission_no"])
                if form["admission_no"] <= 0:
                    raise ValueError
            except ValueError:
                flash("Invalid Admission Number!", "danger")
                return redirect("/students/add")

            # Check if the class is a valid class
            if form["class"] not in CLASSES:
                flash("Invalid Class!", "danger")
                return redirect("/students/add")

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

            flash("Student Successfully Added!", "success")
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
            cursor.execute("UPDATE students SET class = 'Retired' WHERE admission_no = ?", (request.form["admission_no"],))
            connection.commit()
            flash("Student Deleted!", "warning")
            return redirect("/")

    # If it is a get request determine which form to show
    if action == "choose":
        return render_template("admin/students.html")
    elif action == "add":
        return render_template("admin/add_student.html", classes=CLASSES)
    elif action == "remove":
        return render_template("student_search.html", classes=CLASSES, title="Remove Student", action="/students/remove")
    else:
        flash("Invalid Action!", "warning")
        return redirect("/students")


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
                    flash("You must fill all the fields!", "warning")
                    return redirect("/staff/add")
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

            flash("Staff Successfully Added", "success")
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
            flash("Staff Successfully Deleted!", "warning")
            return redirect("/")

    # If it is a get request determine which form to show
    if action == "choose":
        return render_template("admin/staff.html")
    elif action == "add":
        return render_template("admin/add_staff.html")
    elif action == "remove":
        return render_template("staff_search.html", title="Remove Staff", action="/staff/remove")
    else:
        flash("Invalid Action!", "warning")
        return redirect("/staff")


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
            if request.form.get("id") in (None, ""):
                flash("User could not be added!", "danger")
                return redirect("/users/add")
            else:
                user_info["id"] = request.form.get("id")
            
            # Check if the password matches the confirmation
            if user_info["password"] != user_info["confirmation"]:
                flash("Password does not match Confirmation!", "warning")
                return render_template("admin/add_user.html", id=request.form["id"], roles=ROLES)

            # Check if the person chose a valid role
            if user_info["role"] not in ROLES:
                flash("Invalid Role Selected", "danger")
                return render_template("admin/add_user.html", id=request.form["id"], roles=ROLES)

            # Check if the person is already a user
            cursor.execute("SELECT * FROM users WHERE person_id = ?", (user_info["id"],))
            if cursor.fetchone():
                cursor.execute("UPDATE users SET user_role = ? WHERE person_id = ?", (user_info["role"], user_info["id"]))
                connection.commit()
                flash("User Already Exists! User role has been updated.", "warning")
                return redirect("/")

            # Add the user to the database
            password_hash = generate_password_hash(user_info["password"])
            cursor.execute(
                "INSERT INTO users (username, password_hash, user_role, person_id) VALUES (?, ?, ?, ?)",
                (user_info["username"], password_hash, user_info["role"], user_info["id"]))
            connection.commit()

            flash("User Successfully Added!", "success")
            return redirect("/")
        
        if action == "remove":
            cursor.execute("DELETE FROM users WHERE person_id = ?", request.form.get("id"))
            connection.commit()
            flash("User Successfully Removed!", "warning")
            return redirect("/users/remove")
        
        flash("Invalid Action!", "danger")
        return redirect("/users")

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
        flash("Invalid Action!", "danger")
        return redirect("/users")


@app.route("/reports", defaults={"report": None})
@app.route("/reports/<report>")
@is_admin
def reports(report):
    if report is None:
        return render_template("admin/reports.html")
    
    elif report == "unreturned":
        return get_unreturned(title="Unreturned Books", action=None)
    
    elif "damaged" in report:
        cursor.execute("SELECT * FROM damaged JOIN books ON damaged.book_id = books.id ORDER BY report_date DESC LIMIT 100")
        damaged_books = cursor.fetchall()
        return render_template("admin/damage_report.html", books=damaged_books)

    flash("No such Report!", "danger")
    return redirect("/reports")


@app.route("/add_book", methods=["GET", "POST"])
@is_librarian
def add_book():
    if request.method == "POST":
        # Check if the necessary fields are present
        for key in ["title", "quantity"]:
            if request.form.get(key) in ["", None]:
                flash("You must enter the Title and Number of copies!", "warning")
                return redirect("/add_book")
        
        # Create a form_dictionary with cleaned up values
        form = {}
        for key in request.form:
            form[key] = request.form.get(key).strip()
            if form[key] == "":
                form[key] = None
        
        # Check if the book is a reference book
        if form.get("reference"):
            form["reference"] = 1 # True is represented by one
        else:
            form["reference"] = 0 # False is represented by zero
        
        # Check if the number of copies is a valid number
        try:
            form["quantity"] = int(form.get("quantity"))
        except ValueError:
            flash("You entered an invalid Number of Copies!", "danger")
            return redirect("/add_book")
        
        # Add the book into the database
        cursor.execute(
            "INSERT INTO books (title, author, publication_date, quantity, category, reference) VALUES (?, ?, ?, ?, ?, ?)",
            [form.get(key) for key in ("title", "author", "publication_date", "quantity", "category", "reference")])
        connection.commit()

        flash("Book Added Successfully!", "success")
        return redirect("/add_book")
    
    # If it is a get request display a form to add the book
    return render_template("librarian/add_book.html")


@app.route("/borrow", defaults={"person": "choose"})
@app.route("/borrow/<person>", methods=["GET", "POST"])
@is_librarian
def borrow(person):
    # If it is a get request display the appropriate search page for the person
    if request.method == "GET":
        if person == "staff":
            return render_template("staff_search.html", title="Borrow", action="/borrow/staff")
        
        if person == "student":
            return render_template("student_search.html", classes=CLASSES, title="Borrow", action="/borrow/student")
        
        if person == "choose":
            return render_template("librarian/borrow.html")
        
        flash("Invalid Path!", "danger")
        return redirect("/")
    
    # If it is a post request display a page to find the book
    else:
        if person == "staff":
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

            return render_template("staff_results.html", staff=staff, action="/process_borrow/staff", title="Choose Staff")
            
        elif person == "student":
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

            return render_template("student_results.html", students=students, action="/process_borrow/student", title="Choose Student")
        
        else:
            flash("Invalid Path!", "danger")
            return redirect("/")


@app.route("/process_borrow/<person_role>", methods=["POST"])
@is_librarian
def process_borrow(person_role):
    if person_role == "student":
        # Get the student's person_id
        cursor.execute("SELECT person_id FROM students WHERE admission_no = ?", (request.form.get("admission_no"), ))
        student = cursor.fetchone()

        if not student:
            flash("Student Not Found!", "danger")
            return redirect("/borrow")

        return render_template("librarian/book_search.html", action="/process_borrow/choose_book", person_id=student["person_id"], role="student")
    
    elif person_role == "staff":
        return render_template("librarian/book_search.html", action="/process_borrow/choose_book", person_id=request.form.get("id"), role="staff")
    
    # If a person has been chosen display the search form for the book
    elif person_role == "choose_book":
        search_keys = {}

        # Check which values were used in the search
        for key in request.form:
            if key in ["person_id", "person_role"]:
                continue
            if request.form.get(key) not in ["", None]:
                search_keys[key] = request.form.get(key).strip()

        # Generate the query to select relevant students
        beginning = "SELECT * FROM books WHERE "
        conditions = "reference = 0 AND quantity > 0"
        for key in search_keys:
            conditions += " AND "
            conditions += key + " LIKE ?"

        # Query the database to get the relevant students
        cursor.execute(beginning + conditions, ["%" + item + "%" for item in search_keys.values()])
        books = cursor.fetchall()

        # Build a dictionary of extra info to submit with the chosen book
        extra_info = {}
        extra_info["person_id"] = request.form.get("person_id")
        extra_info["person_role"] = request.form.get("person_role")

        return render_template("librarian/book_results.html", books=books, extra_info=extra_info, action="/process_borrow/record", title="Choose Book")
    
    # If a book has been chosen, record the transaction
    elif person_role == "record":
        # Get the date of the borrow and the date before which the book must be returned
        borrow_date = date.today()
        expected_date = borrow_date + timedelta(days=7)

        # Record the transaction in the borrows table
        cursor.execute(
            "INSERT INTO borrows (book_id, person_id, person_role, date_borrowed) VALUES (?, ?, ?, ?)",
            (request.form.get("book_id"), request.form.get("person_id"), request.form.get("person_role"), borrow_date.isoformat())
        )
        
        # Reduce the count of the book in the inventory
        cursor.execute("UPDATE books SET quantity = quantity - 1 WHERE id = ?", (request.form.get("book_id")))

        # Get the borrow id
        borrow_id = cursor.lastrowid

        # Record the borrow as unreturned
        cursor.execute(
            "INSERT INTO unreturned (borrow_id, date_expected) VALUES (?, ?)",
            (borrow_id, expected_date.isoformat())
        )

        connection.commit()

        flash("Borrow Recorded!", "success")
        return redirect("/")
    
    else:
        flash("Invalid Action!", "danger")
        return redirect("/borrow")


@app.route("/return", methods=["GET", "POST"])
@is_librarian
def return_book():
    if request.method == "POST":
        # Update the book count
        cursor.execute("SELECT book_id FROM borrows WHERE id = ?", (request.form.get("borrow_id")))
        book_id = cursor.fetchone()["book_id"]
        cursor.execute("UPDATE books SET quantity = quantity + 1 WHERE id = ?", (book_id,))

        # Remove the borrow from the unreturned table
        cursor.execute("DELETE FROM unreturned WHERE borrow_id = ?", (request.form.get("borrow_id")))

        # Record the date of the return
        return_date = date.today().isoformat()
        cursor.execute("UPDATE borrows SET date_returned = ? WHERE id = ?", (return_date, request.form.get("borrow_id")))

        connection.commit()

        flash("Book Returned Successfully!", "success")
        return redirect("/return")

    # If it is a get request display a list of all unreturned books
    return get_unreturned(title="Return", action="/return")


@app.route("/damage", methods=["POST", "GET"])
@is_librarian
def damage():
    # If it is a get request display a search page
    if request.method == "POST":
        search_keys = {}

        # Check which values were used in the search
        for key in request.form:
            if key in ["person_id", "person_role"]:
                continue
            if request.form.get(key) not in ["", None]:
                search_keys[key] = request.form.get(key).strip()

        # Generate the query to select relevant students
        beginning = "SELECT * FROM books WHERE "
        conditions = "quantity > 0"
        for key in search_keys:
            conditions += " AND "
            conditions += key + " LIKE ?"

        # Query the database to get the relevant students
        cursor.execute(beginning + conditions, ["%" + item + "%" for item in search_keys.values()])
        books = cursor.fetchall()

        # There's no extra info to pass to the template
        extra_info = {}

        return render_template("librarian/book_results.html", books=books, extra_info=extra_info, action="/process_damage", title="Report Damage")
    
    return render_template("librarian/book_search.html", action="/damage")


@app.route("/process_damage", methods=["POST"])
def process_damage():
    cursor.execute("UPDATE books SET quantity = quantity - 1 WHERE id = ?", (request.form.get("book_id")))
    cursor.execute("INSERT INTO damaged (book_id, report_date) VALUES (?, ?)", (request.form.get("book_id"), date.today().isoformat()))
    connection.commit()
    flash("Damage Recorded!", "success")
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged Out!", "success")
    return redirect("/login")


@app.route("/about")
def about():
    flash("There isn't really much to say!", "secondary")
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)