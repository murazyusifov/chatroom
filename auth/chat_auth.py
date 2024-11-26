import mysql.connector

# establishes a connection to the MySQL database using the mysql.connector library
# connects to the database specified by the host, user, password and database parameters
# in this case -- localhost, root, root and chatroom
# the connection object returned can be used to interact with the database
def get_db_connection() :
    return mysql.connector.connect (
        host = "localhost",
        user = "root",
        password = "root",
        database = "chatroom"
    )

# responsible for registering a new user in the users table of the chatroom database
# takes a username and a password as inputs and attempts to insert them into the users table
# if the username is already in use (a duplicate entry), the function will catch the error and return False
# Otherwise, the user is successfully registered and the function returns True
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

# checks if a user exists in the database with the provided username and password
# performs a SELECT query on the users table and returns True if a matching record is found
# if no such record exists, the function returns False, indicating that the authentication has failed
def authenticate_user(username, password) :
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None