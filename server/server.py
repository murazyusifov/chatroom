import socket
import threading
import time
import mysql.connector
import json
from auth.chat_auth import register_user, authenticate_user

clients = {}  # stores the clients and their corresponding info
clients_lock = threading.Lock()
room_last_activity = {}  # tracks the last activity time for each room
is_running = True  # a global flag to control the server state
ROOM_TIMEOUT = 30  # a timeout in seconds for inactivity

"""creates a TCP socket, binds it to the specified port, and starts listening for incoming connections
configured to reuse the address (SO_REUSEADDR)
listens on all available network interfaces (0.0.0.0) and the specified port
returns the socket object for further use"""

def create_socket(port) :
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    host = '0.0.0.0'
    server_address = (host, port)
    s.bind(server_address)
    s.listen(5)
    print(f"Started listening on {host} : {port}")
    return s

"""establishes and returns a connection to the MySQL database with the given parameters
host = "localhost", user = "root", password = "root" and database = "chatroom"
uses mysql.connector.connect() to handle the connection"""

def get_db_connection() :
    return mysql.connector.connect(
        host = "localhost",
        user = "root",
        password = "root",
        database = "chatroom"
    )

"""broadcasts a message to all clients in the specified room, except the sender
updates the last activity time of the current room, and then appends the message to a file specific to the room
sends the message to all other clients in the same room, handling any exceptions if a client cannot be reached"""

def broadcast_message(username, message, room_ID) :
    with clients_lock :
        room_last_activity[room_ID] = time.time()

    with open(f"{room_ID}.txt", "a") as chat_file :
        chat_file.write(message + "\n")

    with clients_lock :
        for client_socket, client_info in clients.items() :
            if client_info['room_ID'] == room_ID and client_info['username'] != username :
                try :
                    client_socket.send(message.encode('utf-8'))
                except Exception as exception :
                    print(f"Error sending the message to {client_info['username']} : {exception}")

"""handles user registration, calling the register_user function to attempt the user registration
if successful, the method sends a success message with a 200 code
if failure, the method sends an error message with a 400 code"""

def handle_registration(client_socket, username, password) :
    if register_user(username, password) :
        client_socket.send(json.dumps({"code" : 200, "username" : username, "message" : "Registration Successful!"}).encode())
    else :
        client_socket.send(json.dumps({"code" : 400, "message" : "Registration Failed!"}).encode())

"""handles user login, calling the authenticate_user function to verify the provided credentials
if successful, the method sends a success message with a 200 code
if failure, the method sends an error message with a 400 code"""

def handle_login(client_socket, username, password) :
    if authenticate_user(username, password) :
        client_socket.send(json.dumps({"code" : 200, "username" : username, "message" : "Authentication Successful!"}).encode())
    else :
        client_socket.send(json.dumps({"code" : 400, "message" : "Authentication Failed!"}).encode())

"""retrieves and returns a list of all available chat rooms from the database
queries the rooms table, fetching the names and IDs of the existing rooms
the result is returned as a list of dictionaries"""

def list_rooms() :
    conn = get_db_connection()
    cursor = conn.cursor(dictionary = True)
    cursor.execute("SELECT room_name, room_ID FROM rooms")
    rooms = cursor.fetchall()
    cursor.close()
    conn.close()
    return rooms

"""allows a user to join a chat room by verifying the room ID and password
checks the rooms table in the database to find the room with the provided room_ID and room_password
if the room exists, the client is added to the clients dictionary, and the last activity time of the room is updated
the client receives a success message with a 200 code and a confirmation of joining the room
then attempts to load and send the chatting history of the room (from a file named after the room ID)
if the room file exists, the chatting history is sent; otherwise, the user is informed
if the room does not exist or the credentials are wrong, the client receives an error message with a 400 code"""

def join_room(client_socket, username, room_ID, room_password) :
    conn = get_db_connection()
    cursor = conn.cursor(dictionary = True)
    cursor.execute("SELECT * FROM rooms WHERE room_ID = %s AND room_password = %s", (room_ID, room_password))
    room = cursor.fetchone()
    cursor.close()
    conn.close()

    if room is not None :
        with clients_lock :
            clients[client_socket] = {'username' : username, 'room_ID' : room_ID}

        with clients_lock :
            room_last_activity[room_ID] = time.time()

        client_socket.send(json.dumps({"code" : 200, "message" : f"Joined room {room_ID} successfully!"}).encode())
        print(f"{username} joined room {room_ID}.")
    else :
        client_socket.send(json.dumps({"code" : 400, "message" : "Invalid room ID or password!"}).encode())
        return

    try :
        with open(f"{room_ID}.txt", "r") as chat_file :
            chat_history = chat_file.read()
            if chat_history :
                client_socket.send(f"Chatting History : \n{chat_history}\n".encode())
            else :
                client_socket.send(f"No Chatting History\n".encode())
    except FileNotFoundError :
        client_socket.send(f"No Chatting History\n".encode())

"""creates a new room in the database with the provided room_name, room_description and room_password
attempts to insert the room data into the rooms table
if successful, the method sends a 200 success message to the client
if the room already exists (due to an IntegrityError), the method sends a 400 failure message to the client"""

def handle_create_room(client_socket, room_name, room_description, room_password) :
    conn = get_db_connection()
    cursor = conn.cursor()
    try :
        cursor.execute("INSERT INTO rooms (room_name, room_description, room_password) VALUES (%s, %s, %s)",
                       (room_name, room_description, room_password))
        conn.commit()
        client_socket.send(json.dumps({"code" : 200, "message" : "Room Creation Successful!"}).encode())
    except mysql.connector.IntegrityError :
        client_socket.send(json.dumps({"code" : 400, "message" : "Room Creation Failed!"}).encode())
    finally :
        cursor.close()
        conn.close()

"""deletes a room from the database based on the provided room_ID
attempts to delete the room from the rooms table
if successful, the method sends a 200 success message to the client
if no room is deleted (invalid room_ID), the method sends a 400 failure message to the client"""

def handle_delete_room(client_socket, room_ID) :
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rooms WHERE room_ID = %s", (room_ID,))
    conn.commit()
    if cursor.rowcount > 0 :
        client_socket.send(json.dumps({"code" : 200, "message" : "Room Deletion Successful!"}).encode())
    else:
        client_socket.send(json.dumps({"code" : 400, "message" : "Room Deletion Failed!"}).encode())
    cursor.close()
    conn.close()

"""processes the client actions received over the socket, listening for commands like
registering, logging in, joining rooms, creating or deleting rooms, listing rooms, sending messages and disconnecting
Registration/Authentication : calls the handle_registration or handle_login functions based on the action
Room Operations : joining rooms (join_room), creating rooms (handle_create_room) and deleting rooms (handle_delete_room)
Message Sending : sends messages in the room using the broadcast_message function if the client is in a room
Listing Available Rooms : returns a list of available rooms with the list_rooms functions
Disconnecting : cleans up by removing the client from the clients dictionary and deleting the room activity data
if any error occurs (connection issues), the client is disconnected from the server"""

def handle_client(client_socket) :
    username = None
    room_ID = None

    while True :
        try :
            action = client_socket.recv(1024).decode('utf-8')
            if not action :
                break

            data = json.loads(action)

            if data["action"] == "register" :
                username = data["username"]
                password = data["password"]
                handle_registration(client_socket, username, password)

            elif data["action"] == "login" :
                username = data["username"]
                password = data["password"]
                handle_login(client_socket, username, password)

            elif data["action"] == "join_room" :
                room_ID = data["room_ID"]
                room_password = data["room_password"]
                join_room(client_socket, username, room_ID, room_password)

            elif data["action"] == "create_room" :
                room_name = data["room_name"]
                room_description = data["room_description"]
                room_password = data["room_password"]
                handle_create_room(client_socket, room_name, room_description, room_password)

            elif data["action"] == "delete_room" :
                room_ID = data["room_ID"]
                handle_delete_room(client_socket, room_ID)

            elif data["action"] == "list" :
                rooms = list_rooms()
                client_socket.send(json.dumps({"rooms" : rooms}).encode())

            elif data["action"] == "send_message" :
                message = data["message"]
                if room_ID :
                    formatted_message = f"{username} >> {message}"
                    broadcast_message(username, formatted_message, room_ID)

            elif data["action"] == "disconnect" :
                print(f"{username} disconnected...")
                with clients_lock :
                    if client_socket in clients :
                        del clients[client_socket]
                        if room_ID in room_last_activity :
                            del room_last_activity[room_ID]

        except (ConnectionAbortedError, ConnectionResetError) as exception :
            print(f"Connection error with client {username if username else 'unknown'} : {exception}")
            break
        except Exception as exception :
            print(f"Error handling client {username if username else 'unknown'} : {exception}")
            break

"""checks for inactive rooms and disconnects users from rooms that have been inactive for too long
continuously runs in a loop, checking the room_last_activity dictionary for the last activity timestamp of each room
if the time since the last activity exceeds a defined timeout (ROOM_TIMEOUT)
the function sends a disconnect message to all users in the room and removes them from the clients dictionary"""

def check_inactivity() :
    while is_running :
        current_time = time.time()
        with clients_lock :
            for room_ID, last_activity in list(room_last_activity.items()) :
                if current_time - last_activity > ROOM_TIMEOUT :
                    print(f"Room {room_ID} has been inactive for too long. Disconnecting its users...")
                    for client_socket, client_info in list(clients.items()) :
                        if client_info['room_ID'] == room_ID :
                            try :
                                client_socket.send(f"Room {room_ID} has been inactive for too long. You are being disconnected...\n".encode())
                                client_socket.close()
                            except Exception as exception :
                                print(f"Error sending the message to {client_info['username']} : {exception}")
                            del clients[client_socket]
                    del room_last_activity[room_ID]
        time.sleep(5)

"""starts the server, accepting client connections and handling them in separate threads
it also monitors for inactivity and allows the server to be shut down
the server socket is created on port 3169, and the server begins listening for incoming client connections
client handling : a new thread is spawned for each client, calling handle_client to process their requests
another thread runs check_inactivity to manage the room activity
the server listens for a "shutdown" command, when issued --
closes the server socket, notifies all connected clients, disconnects them and clears the clients dictionary"""

def start_server() :
    global is_running
    port = 3169
    server_socket = create_socket(port)
    print("Server started, waiting for connections...")

    def accept_clients() :
        global is_running
        while is_running :
            try :
                client_sock, addr = server_socket.accept()
                print(f"\nConnection from {addr}")
                threading.Thread(target = handle_client, args = (client_sock,)).start()
            except OSError :
                if not is_running :
                    break

    threading.Thread(target = accept_clients, daemon = True).start()
    threading.Thread(target = check_inactivity, daemon = True).start()

    while True :
        command = input("Enter 'shutdown' to stop the server : ").strip().lower()
        if command == "shutdown" :
            is_running = False
            server_socket.close()
            print("Server is shutting down...")

            log_shutdown_time()

            with clients_lock :
                for client_socket in list(clients.keys()) :
                    try :
                        client_socket.send("Server is shutting down. You will be disconnected...\n".encode())
                    except Exception as exception :
                        print(f"Error notifying the client : {exception}")
                    finally :
                        client_socket.close()
                clients.clear()
            print("All clients have been disconnected...")
            break

def log_shutdown_time() :
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open("logs.txt", "a") as log_file :
        log_file.write(f"SERVER was closed at {current_time}.\n")

if __name__ == "__main__" :
    try :
        start_server()
    except KeyboardInterrupt :
        print("\nServer shut down by a keyboard interrupt...\n")
    except Exception as e :
        print(f"Something went wrong. Shutting down...{e}")
