# Library Management System

CS/SE 3347.008 Database Systems Programming Project

---

## Running the Application

Clone the repository, then from the project root run:

```bash
python3 libms.py
```

This will start the main application.

---

## Environment Configuration

The application expects a `.env` file in the project directory with your MySQL connection details:

```env
MYSQL_HOST='localhost'
MYSQL_USER='root'
MYSQL_PASS=''
MYSQL_DB='LIBMS'
```

Adjust these values to match your local MySQL setup.

---

## Testing the Search Module

You can test the search functionality directly from the command line.

General usage:

```bash
python3 -m app.search "<search-term>"
```

The search term can match:

* ISBN
* Title
* Author name(s)

Example:

```bash
python3 -m app.search "Harry Potter"
```
