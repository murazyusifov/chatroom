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
def authenticate_user(username, password):
    try:
        # Establish the connection to the database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Execute the query to find the user with the provided username and password
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))

        # Fetch a single result (user) from the query
        result = cursor.fetchone()

        # Close the cursor and connection after the operation
        cursor.close()
        conn.close()

        # Return True if the user was found, otherwise False
        return result is not None

    except mysql.connector.Error as err:
        # Log the MySQL error (for debugging purposes)
        print(f"MySQL error during authentication: {err}")
        return False
    except Exception as e:
        # Log any unexpected errors
        print(f"Unexpected error during authentication: {e}")
        return False
