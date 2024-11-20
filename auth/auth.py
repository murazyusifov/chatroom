import mysql.connector

"""Creates a connection to the MySQL database using the mysql.connector library.
It connects to the specified database using the provided host, user, password, and database credentials.
In this case, it connects to 'localhost', with 'root' as both the username and password, and the 'chatroom' database.
The connection object returned allows interaction with the database."""

def get_db_connection() :
    return mysql.connector.connect (
        host = "localhost",
        user = "root",
        password = "root",
        database = "chatroom"
    )

"""Handles the registration of a new user in the 'users' table of the 'chatroom' database.
It accepts a username and password, then inserts them into the table.
If the username already exists (causing a duplicate entry), the function catches the error and returns False.
If the registration is successful, it returns True."""

def register_user(username, password) :
    conn = get_db_connection()
    cursor = conn.cursor()
    try :
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        return True
    except mysql.connector.IntegrityError :
        return False
    finally :
        cursor.close()
        conn.close()

"""Verifies if a user exists in the database by checking the provided username and password.
Performs a SELECT query on the 'users' table and returns True if a matching record is found.
If no match is found, it returns False, indicating failed authentication."""

def authenticate_user(username, password) :
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None
