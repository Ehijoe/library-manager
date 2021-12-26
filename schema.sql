CREATE TABLE users (
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    user_role TEXT NOT NULL,
    id INTEGER PRIMARY KEY NOT NULL,
    person_id NOT NULL
);

CREATE TABLE people (
    id INTEGER PRIMARY KEY NOT NULL,
    first_name TEXT NOT NULL,
    middle_name TEXT,
    surname TEXT NOT NULL,
    birthdate TEXT
);

CREATE TABLE staff (
    id INTEGER PRIMARY KEY NOT NULL,
    person_id INT UNIQUE NOT NULL,
    job_title TEXT NOT NULL
);

CREATE TABLE students (
    admission_no INT PRIMARY KEY NOT NULL,
    person_id INT UNIQUE NOT NULL,
    class TEXT NOT NULL
);

CREATE TABLE books (
    id INTEGER PRIMARY KEY NOT NULL,
    title TEXT NOT NULL,
    author TEXT,
    publication_date TEXT,
    quantity INT NOT NULL,
    category TEXT,
    reference INT
);

CREATE TABLE borrows (
    id INTEGER PRIMARY KEY NOT NULL,
    book_id INT NOT NULL,
    person_id INT NOT NULL,
    person_role TEXT NOT NULL,
    date_borrowed TEXT NOT NULL,
    date_returned TEXT
);

CREATE TABLE unreturned (
    borrow_id INT NOT NULL,
    date_expected INT NOT NULL
);

CREATE TABLE damaged (
    book_id INT NOT NULL,
    report_date TEXT NOT NULL
);