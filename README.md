
# ***School Library Manager***

A system to keep track of books borrowed in a school library.

------------

# User Roles

There are two types of users in the system, *librarians* and *administrators*

## Administrator

An administrative officer of the school. Administrators can manage students, staff and users.

Administrators can:

- [x] Register new students
- [x] Delete students who are no longer in the school [^1]
- [x] Register new staff
- [x] Remove staff who no longer work in the school [^1]
- [x] Add new users
- [x] Delete existing users
- [ ] View some reports

## Librarian

A librarian who can records all borrowed books.

Librarians can:

- [ ] View a list of unreturned books
- [ ] Record a new borrow transaction
- [ ] Record the return of a book
- [ ] Report a book as damaged or lost
- [ ] Add new books to the inventory

------------

# Files

------------

## schema.sql

A file containing all the SQL commands used to create the database. It is run immediately the database is created.

### Tables

#### people

A table that keeps the records of all the people involved in the system.
It's columns are:

- **id:** The primary key
- **first_name**
- **middle_name**
- **surname**
- **birthdate:** uses the ISO8601 date format

#### users

A table that stores the information of all the users who can log in to the system.
It's columns are:

- **username:** The username used in logging in
- **password_hash:**: The hashed password of the user
- **user_role:** A string that identifies whether the user is an administrator or librarian
- **id:** Primary key
- **person_id:** A Foreign key that links to the id in the people table

#### staff

A table that stores the data of the staff of the school.
It's columns are:

- **id:** Primary key
- **person_id:** A Foreign key that links to the id in the people table
- **job_title**

#### students

A table that stores the data of the students of the school.
It's columns are:

- **admission_no:** Primary key
- **person_id:** A Foreign key that links to the id in the people table
- **class**

#### books

A table that stores the data of all the books in the school library.
It's columns are:

- **id:** Primary key
- **title**
- **publication_date:** Uses the ISO8601 date format
- **qauntity:** The number of copies of this book in the inventory
- **category**
- **reference:** An integer that is 1 if the book is a reference book and 0 if it is not. A reference book cannot be borrowed

#### borrows

A table that stores all the records of borrowing. The records are permanent.
It's columns are:

- **id:** Primary key
- **book_id:** A foreign key to identify the book being borrowed
- **person_id:** A foreign key to identify the person borrowing the book
- **person_role:** Whether the person was a member of staff or a student when the book was borrowed
- **date_borrowed:** uses the ISO8601 date format
- **date_returned** uses the ISO8601 date format. If the book is not returned, the value is NULL

#### unreturned

This is a table that stores keeps track of all the books that have been borrowed. This is a separate table to prevents wasting time searching the borrows table as the number of borrows increases.

- **borrow_id:** A foreign key that links to the borrows table
- **date_expected:** Uses the ISO8601 date format. This date is on week after the book was borrowed.

#### damaged

This table keeps record of all the books that have been damaged

- **book_id:** A foreign key that links to the id in the books table
- **report_date:** Uses the ISO8601 date format

------------

## static

The css and javascript files used in the project are stored in this folder.

------------

## templates

This folder contains the html templates used in the project.

------------

## app.py

### Configuration

#### Global variables

- ***CLASSES:*** A list that contains all the classes that students can be in.

- ***ROLES:*** A dictionary with the roles that users can have and their proper representations.

#### Database Connection

An sqlite database called `library.sqlite` is connected to. If it was just created, then `schema.sql` is run.  A cursor to query the database is also created.

### Supporting functions

#### is_admin

This is a decorator to ensure that the user is an administrator. It checks the user's session to see if the role is set to `"admin"`.

### Routes

#### login

[^1]: The students and staff aren't actually deleted to preserve records of the books they have borrowed.
