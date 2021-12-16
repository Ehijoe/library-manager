# Import external libraries
from flask import Flask
import sqlite3
import os

# App configuration
app = Flask(__name__)

db = "library.db"

# Check if database exists
database_exists = os.path.isfile(db)

# Connect to the database
connection = sqlite3.connect(db)

# If the database was just created, create the tables.
if database_exists:
    print("Database exists.")
else:
    with open("schema.sql") as schema:
        


@app.route("/")
def index():
    return "<p>TODO!!</p>"


if __name__ == "__main__":
    app.run(debug=True)