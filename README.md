
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
- [x] View Unreturned books
- [x] View Damaged books

## Librarian

A librarian who can records all borrowed books.

Librarians can:

- [x] View a list of unreturned books [^2]
- [x] Record a new borrow transaction
- [x] Record the return of a book
- [x] Report a book as damaged or lost
- [x] Add new books to the inventory

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

### Both Users

#### base.html

This is the base template that all other templates inherit from. It links the bootstrap css and javascript files. It has two blocks:

- title: This contains the title to be displayed in the title head element and in a heading tag in the main body.

- body: This is the main content of the page.

It also includes a navbar for easy navigation that changes depending on the role of the user logged in.

It has a footer that displays dismissible flashed messages as alerts.

#### login.html

This template contains the login form. It submits to the `/login` route.

#### staff_search.html

This template contains a form that could be used to search for a member of staff. It takes two variables:

- title: The Title of the page to be displayed.
- action: The route that the form is submitted to.

#### staff_results.html

This template displays a list of staff, each with a button to carry out some action. The button submits the `person_id` of the member of staff to a specified route. It takes the variables:

- title: The title of the page to be displayed. It also serves as the label for the button.
- staff: A list of the staff that are to be displayed.
- action: The route to which the selected `person_id` will be submitted to.

#### student_search.html

This template contains a form that could be used to search for a student. It takes two variables:

- title: The Title of the page to be displayed.
- action: The route that the form is submitted to.
- classes: A list of all the classes a student could be in.

#### student_results.html

This template displays a list of students, each with a button to carry out some action. The button submits the `admission_no` of the student to a specified route. It takes the variables:

- title: The title of the page to be displayed. It also serves as the label for the button.
- staff: A list of the staff that are to be displayed.
- action: The route to which the selected `admission_no` will be submitted to.

#### unreturned.html

This template displays a list of unreturned books and optionally a button submits the `borrow_id` to a specified route. It takes the variables:

- title: The title of the page to be displayed. It also serves as the label for the button if any.
- action: The route to which the `borrow_id` will be submitted.
- student_borrows: A list of information (in the form of a dictionary) about books borrowed by students.
- staff_borrows: A list of information (in the form of a dictionary) about books borrowed by staff.

### Admin Only

#### add_staff.html

This template displays a form for a member of staff to be added. The form is submitted to `/staff/add`.

#### add_student.html

This template displays a form for a student to be added. The form is submitted to `/students/add`. It takes the variable:

- classes: A list of the classes a student can possibly be in.

#### add_user.html

This template displays a form for a user to be added. The form is submitted to `/users/add`. It takes the variable:

- roles: A list of the roles a user can play.

#### damage_report.html

This template displays a list of books that have been reported to be damaged. It takes the variable:

- books: A list of the books that were reported damaged along with the date it was reported.

#### home.html (admin)

This template shows a list of the actions the admin can take:

- Manage Students `/students`
- Manage Staff `/staff`
- Manage Users `/users`
- View Reports `/reports`

#### reports.html

A menu to select the reports to view:

- Unreturned Books `/reports/unreturned`
- Damage Report `/reports/damaged`

#### staff.html

A menu to select the action to carry out related to staff:

- Add Staff `/staff/add`
- Remove Staff `/staff/remove`

#### student.html

A menu to select the action to carry out related to students:

- Add Student `/student/add`
- Remove Student `/student/remove`

#### users.html

A menu to select the action to carry out related to users:

- Add User `/users/add`
- Remove Remove `/users/remove`

#### user_list.html

This template displays a list of users, each with a button to carry out some action. The button submits the `id` of the user to a specified route. It takes the variables:

- title: The title of the page to be displayed. It also serves as the label for the button.
- users: A list of the users that are to be displayed.
- action: The route to which the selected `person_id` will be submitted to.

### Librarian Only

#### home.html (librarian)

This template shows a list of the actions the admin can take:

- Add Book `/add_book`
- Borrow `/borrow`
- Return `/return`
- Report Damage `/damage`

#### add_book.html

This template diaplays a form for adding books to the inventory. It is submitted to `/add_book`.

#### book_search.html

This template displays a form for searching for a book. It takes the variables:

- action: The route to which the form will be submitted.
- role: If a person has previously been selected, this will be either 'staff' or 'student'.
- person_id: If a person has previously been selected, this will be their `person_id`

#### book_results.html

This template displays a list of books along with a button that submits the `book_id` to a specified route. It's variables are:

- title: The title of the page to be displayed. It also serves as the label for the button.
- action: The route to which the form will be submitted.
- books: The list of books to be displayed.
- extra_info: A dictionary of extra information to be submitted alongside the `book_id`.

#### borrow.html

A menu to select the kind of person who is borrowing a book:

- Student Borrow `/borrow/student`
- Staff Borrow `/borrow/staff`

------------

## app.py

### Configuration

#### Global variables

- ***CLASSES:*** A list that contains all the classes that students can be in.

- ***ROLES:*** A dictionary with the roles that users can have and their proper representations.

#### Database Connection

An sqlite database called `library.sqlite` is connected to. If it was just created, then `schema.sql` is run. A cursor to query the database is also created.

When the database is created, a test person is inserted and then linked to two users, 'admin' and 'librarian', both with the password 'test'.

### Supporting functions

#### is_admin

This is a decorator to ensure that the user is an administrator. It checks the user's session to see if the role is set to `"admin"`.

#### is_librarian

This is a decorator to ensure that the user is an librarian. It checks the user's session to see if the role is set to `"librarian"`.

#### get_unreturned

It takes two arguments:

- `title`: The title of the rendered page and the label of the button.
- `action`: The route to which the button associated with each unreturned book submits data.

Queries the database to get the list of unreturned books and using that returns a rendered `'unreturned.html'` template with the title, `title` which submits the form to `action`.

#### get_url

A replacement for `url_for` which returns `None` if a `BuildError` is encountered. This is necessary for url paths with variables not to break the `'base.html'` template.

#### heading_filter

A filter that formats headings by replacing underscores with spaces and capitalizing every word.

### Routes

#### index (`/`)

Renders the appropriate home page template depending on the role of the user. The user is redirected to the login page if not logged in.

#### login (`/login`)

- **GET:** Renders the login page.

- **POST:** Checks the user's credentials and redirects to the index if they are correct. Otherwise the user is redirected back to the login.

#### students (`/students/<action>`)

The default value of `action` is 'choose'.

- `/students/choose` displays a menu for choosing an action.

- `/students/add` displays a form for entering the student's information. When the form is submitted, the data is validated and the student is added to the database.

- `/students/remove` displays a form for searching for a student. The matching students are then displayed along with a button for submitting their `admission_no` to `/students/delete`.

- `/students/delete` sets the `class` of the student whose `admission_no` was received to `'Retired'`.

#### staff (`/staff/<action>`)

The default value of `action` is 'choose'.

- `/staff/choose` displays a menu for choosing an action.

- `/staff/add` displays a form for entering the staff member's information. When the form is submitted, the data is validated and the staff member is added to the database.

- `/staff/remove` displays a form for searching for a staff member. The matching staff are then displayed along with a button for submitting their `person_id` to `/staff/delete`.

- `/staff/delete` sets the `job_title` of the staff member whose `person_id` was received to `'Retired'`.

#### users (`/users/<action>`)

The default value of `action` is 'choose'.

- `/users/choose` displays a menu for choosing an action.

- `/users/add` (GET) displays a form for searching for a staff member to add as a user. The form is submitted to `/users/add_list`.

- `/users/add_list` (POST) displays a list of staff members that match the search. Buttons corresponding to each member of staff submit their `person_id` to `/users/add`.

- `/users/add` (POST) displays a form that asks for the username, password and role of the user repeatedly until they are entered and submits to itself. When the details are entered, it enters the user into the database using the `person_id` supplied from `/users/add_list` and redirects the user to the home page.

- `/users/remove` displays a list of the users currently registered along with buttons that submit the `person_id` of the user to itself. If a `person_id` is submitted to it, it deletes the user with that `person_id`.

#### reports (`/reports/<report>`)

A list of reports for the admin to see.

#### add_book (`/add_book`)

Displays a form for adding books which updates the database when submitted.

#### borrow (`/borrow/<person>`)

Allows the person who is borrowing the book to be searched for and submits the `person_id` or `admission_no` to process_borrow.

#### process_borrow (`/process_borrow/<person_role>`)

Records the borrow in the database and redirects to the home page.

#### damage (`/damage`)

Brings a form to search for the book that is damaged and generates a list of the books that meet the search criteria with buttons that the `book_id` submit to `/process_damage`.

#### process_damage (`/process_damage`)

Records the damage in the database and redirects to the home page.

#### logout (`/logout`)

Logs the user out and redirects to the login page.

#### about (`/about`)

Not yet done.

[^1]: The students and staff aren't actually deleted to preserve records of the books they have borrowed.
[^2]: The list of unreturned books is displayed in the page for returning books along with buttons to return the books.
