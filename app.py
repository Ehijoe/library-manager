# Import external libraries
from sqlite3.dbapi2 import Cursor
from flask import Flask
import sqlite3
import os

# App configuration
app = Flask(__name__)

db = "library.sqlite"

# Check if database exists
database_exists = os.path.isfile(db)

# Connect to the database
connection = sqlite3.connect(db)
cursor = connection.cursor()

# If the database was just created, create the tables.
if database_exists:
    print("Database exists.")
else:
    with open("schema.sql") as schema:
        cursor.executescript(schema.read())


@app.route("/")
def index():
    return "<p>TODO!!</p>"


if __name__ == "__main__":
    app.run(debug=True)