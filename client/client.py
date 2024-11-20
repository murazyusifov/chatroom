import socket
import json
import threading

class ChatClient :
    def __init__(self) :
        self.client_sock = None                   # the client socket object to be created
        self.username = None                      # to store the username when logged in
        self.listener_event = threading.Event()   # the event to signal the listener thread to stop
        self.listener_thread = None               # the listener thread object

    def create_socket(self) :
        """Establishes a socket connection to the server
            Creates a socket object using the AF_INET (IPv4) address family and SOCK_STREAM (TCP) type
            Attempts to connect to the server at localhost on port 3169
            If the connection succeeds, a confirmation message is printed
            If an error occurs (e.g., server unavailable), it handles the exception, closes the socket, and exits the program"""

        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('localhost', 3169)
        try :
            self.client_sock.connect(server_address)
            print("Connected to the server...")
        except socket.error as exception :
            print(f"Error connecting to the server : {exception}")
            self.client_sock.close()
            exit(1)
        return self.client_sock


    def register(self) :
        """Registers a new user with the server by sending their username and password
Prompts the user for input, then creates an action dictionary containing the registration details
Sends this data to the server in JSON format and waits for the server's response
Returns the server response as a Python dictionary"""

        username = input("Enter a username to register : ")
        password = input("Enter a password : ")
        action = {"action" : "register", "username" : username, "password" : password}
        try :
            self.client_sock.send(json.dumps(action).encode('utf-8'))
            register_response = self.client_sock.recv(1024).decode('utf-8')
            print("Registration Response : ", register_response)
            return json.loads(register_response)
        except (socket.error, ConnectionResetError) as exception :
            print(f"Error registering the user : {exception}")
            self.client_sock.close()
            exit(1)


    def login(self) :
        """Authenticates an existing user by verifying their username and password
Prompts the user to input their login credentials and sends them to the server in a JSON-encoded dictionary
Waits for the server's response, which is then printed
Returns the server response as a Python dictionary"""
        username = input("Enter your username : ")
        password = input("Enter your password : ")
        action = {"action" : "login", "username" : username, "password" : password}
        try :
            self.client_sock.send(json.dumps(action).encode('utf-8'))
            login_response = self.client_sock.recv(1024).decode('utf-8')
            print("Authentication Response : ", login_response)
            return json.loads(login_response)
        except (socket.error, ConnectionResetError) as exception :
            print(f"Error authenticating the user : {exception}")
            self.client_sock.close()
            exit(1)


    def list_rooms(self) :
        """Requests a list of available chat rooms from the server
Sends a request to the server using a JSON-encoded dictionary with the action type set to 'list'
Waits for the server response, which includes a list of rooms
Decodes and prints the room details"""
        action = {"action" : "list"}
        try :
            self.client_sock.send(json.dumps(action).encode('utf-8'))
            list_rooms_response = self.client_sock.recv(1024).decode('utf-8')
            available_rooms = json.loads(list_rooms_response)["rooms"]
            print("\nAvailable Rooms : ")
            for room in available_rooms :
                print(f"Room : {room['room_name']}, ID : {room['room_ID']}")
            return available_rooms
        except (socket.error, ConnectionResetError) as exception :
            print(f"Error fetching the list of available rooms : {exception}")
            self.client_sock.close()
            exit(1)


    def create_room(self) :
        """Creates a new chat room by collecting the room name, description, and password
Sends this data to the server in a JSON-encoded dictionary with the action type set to 'create_room'
Waits for the server's response and prints it"""
        room_name = input("Enter the name of the new room : ")
        room_description = input("Enter the description of the new room : ")
        room_password = input("Enter the password of the new room : ")
        action = {"action" : "create_room", "room_name" : room_name,
                  "room_description" : room_description, "room_password" : room_password}
        try :
            self.client_sock.send(json.dumps(action).encode('utf-8'))
            create_response = self.client_sock.recv(1024).decode('utf-8')
            print("Room Creation Response : ", create_response)
        except (socket.error, ConnectionResetError) as exception :
            print(f"Error creating the room : {exception}")
            self.client_sock.close()
            exit(1)


    def delete_room(self) :
        """Deletes a chat room using its room ID
Prompts the user to input the room ID they wish to delete
Sends the room ID to the server in a JSON-encoded dictionary with the action type set to 'delete_room'
Waits for the server's response and prints whether the deletion was successful or not"""
        room_ID = input("Enter the ID of the room to delete : ")
        action = {"action" : "delete_room", "room_ID" : room_ID}
        try :
            self.client_sock.send(json.dumps(action).encode('utf-8'))
            delete_response = self.client_sock.recv(1024).decode('utf-8')
            print("Room Deletion Response : ", delete_response)
        except (socket.error, ConnectionResetError) as exception :
            print(f"Error deleting the room : {exception}")
            self.client_sock.close()
            exit(1)


    def join_room(self) :
        """Allows the user to join an existing chat room by entering the room ID and password
Prompts the user for these inputs and sends the data to the server in a JSON-encoded dictionary with the action type set to 'join_room'
Waits for the server's response, which indicates whether the user was successfully added to the room"""
        room_ID = input("Enter a room ID to join : ")
        room_password = input("Enter the room password to join : ")
        action = {"action" : "join_room", "room_ID" : room_ID, "room_password" : room_password}
        try :
            self.client_sock.send(json.dumps(action).encode('utf-8'))
            join_response = self.client_sock.recv(1024).decode('utf-8')
            print("Join Room Response : ", join_response)
            return json.loads(join_response)
        except (socket.error, ConnectionResetError) as exception :
            print(f"Error joining the room : {exception}")
            self.client_sock.close()
            exit(1)

    def listen_for_messages(self) :
        """Listens for incoming messages from the server in a non-blocking manner
The listener runs in a loop as long as the listener_event is not set, with a timeout of 1 second
If a message is received, it is printed; otherwise, the loop continues without blocking"""
        while not self.listener_event.is_set() :
            try :
                self.client_sock.settimeout(1.0)
                response = self.client_sock.recv(1024).decode('utf-8')
                if response == "" :
                    break
                else :
                    print(response)
            except socket.timeout :
                if self.listener_event.is_set() :
                    break


    def chat(self) :
        """Manages the chatting session by starting the listener thread and enabling the user to send messages
If the user types 'quit', a disconnect action is sent, the listener thread is stopped, and the user exits the chat
Otherwise, the message is sent to the server"""
        self.listener_event.clear()
        self.listener_thread = threading.Thread(target = self.listen_for_messages, daemon = True)
        self.listener_thread.start()

        while True :
            message = input()
            if message.lower() == 'quit' :
                action = {"action" : "disconnect"}
                self.client_sock.send(json.dumps(action).encode('utf-8'))
                print("You left the room...")

                # stop the listener thread by setting the event
                self.listener_event.set()

                # wait for the listener thread to finish
                self.listener_thread.join()

                break
            else :
                action = {"action" : "send_message", "message" : message}
                self.client_sock.send(json.dumps(action).encode('utf-8'))

    def main(self) :
        """Handles the main flow of the program by guiding the user through registration, login, and interacting with the chat system
If logged in, the user can create, delete, list, or join rooms
Admin privileges are required to create or delete rooms, and regular users are denied access to these actions"""
        isAdmin = False

        while True :
            if self.username is None :
                choice = input("Do you want to (r)egister or (l)ogin? ").lower()
                if choice == 'r' :
                    registration_response = self.register()
                    if registration_response.get("code") == 200 :
                        self.username = registration_response.get("username")
                elif choice == 'l' :
                    authentication_response = self.login()
                    if authentication_response.get("code") == 200 :
                        self.username = authentication_response.get("username")
                        isAdmin = (self.username == 'admin')
                else :
                    print("Invalid Choice!")
            else :
                command = input("\nEnter a command (list, create, delete, join, exit) : ").lower()
                if command == 'create' :
                    if isAdmin :
                        self.create_room()
                    else :
                        print("Permission Denied. Only Admin!")
                elif command == 'delete' :
                    if isAdmin :
                        self.delete_room()
                    else :
                        print("Permission Denied. Only Admin!")
                elif command == 'list' :
                    self.list_rooms()
                elif command == 'join' :
                    join_resp = self.join_room()
                    if join_resp.get("code") == 200 :
                        self.chat()
                elif command == 'exit' :
                    print("Exiting...")
                    self.client_sock.close()
                    break
                else :
                    print("Invalid Command!")

if __name__ == "__main__" :
    try :
        client = ChatClient()    # create a client instance
        client.create_socket()   # create the socket connection
        client.main()            # start the main interaction loop
    except KeyboardInterrupt :
        print("\nBye...")
    except Exception as e :
        print(f"Something went wrong. Shutting down... {e}")
