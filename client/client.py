import socket
import json
import threading

class ChatClient :
    def __init__(self) :
        self.client_sock = None                   # the client socket object to be created
        self.username = None                      # to store the username when logged in
        self.listener_event = threading.Event()   # the event to signal the listener thread to stop
        self.listener_thread = None               # the listener thread object

    # used to create a socket object and connect the client to the server
    # creates a new socket object using the AF_INET address family (IPv4) and the SOCK_STREAM type (TCP)
    # attempts to connect to the server at localhost on port 3169
    # if the connection is successful, the method prints a confirmation message
    # if an error occurs during the connection (the server is unavailable),
    # the method catches the exception, prints an error message, closes the socket and exits the program
    def create_socket(self) :
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

    # allows a new user to register with the server by sending their credentials
    # prompts the user for a username and a password
    # creates an action dictionary containing the registration request, and sends it to the server in JSON format
    # then waits for the server response, which is received and printed
    # returns the response as a Python dictionary
    def register(self) :
        username = input("Enter a username to register : ")
        password = input("Enter a password : ")
        action = {"action" : "register", "username" : username, "password" : password}
        try :
            self.client_sock.send(json.dumps(action).encode('utf-8'))
            register_response = self.client_sock.recv(1024).decode('utf-8')
            register_data = json.loads(register_response)
            print(register_data["message"])
            return json.loads(register_response)
        except (socket.error, ConnectionResetError) as exception :
            print(f"Error registering the user : {exception}")
            self.client_sock.close()
            exit(1)

    # used to authenticate an existing user by sending their username and password to the server
    # prompts the user for their login credentials
    # creates an action dictionary containing the login request, and sends it to the server in JSON format
    # the server response is then received and printed
    # returns the response as a Python dictionary
    def login(self) :
        username = input("Enter your username : ")
        password = input("Enter your password : ")
        action = {"action" : "login", "username" : username, "password" : password}
        try :
            self.client_sock.send(json.dumps(action).encode('utf-8'))
            login_response = self.client_sock.recv(1024).decode('utf-8')
            login_data = json.loads(login_response)
            print(login_data["message"])
            return json.loads(login_response)
        except (socket.error, ConnectionResetError) as exception :
            print(f"Error authenticating the user : {exception}")
            self.client_sock.close()
            exit(1)

    # requests a list of available chat rooms from the server
    # sends an action dictionary with the action type set to "list"
    # after sending the request, the method waits for the server response
    # then decodes the response, extracts the room information and prints out the available rooms
    def list_rooms(self) :
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

    # allows the user to create a new chat room
    # prompts the user to enter the room name, description and password
    # sends this data to the server in a JSON-encoded dictionary with the action type set to "create_room"
    # the server response is then received and printed
    def create_room(self) :
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

    # allows the user to delete a chat room by its ID
    # prompts the user for the room ID to be deleted
    # sends the ID to the server in a JSON-encoded dictionary with the action type set to "delete_room"
    # the server response, indicating the success or failure of the deletion, is then printed
    def delete_room(self) :
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

    # allows the user to join an existing chat room by providing the room ID and password
    # prompts the user to input the room ID and password
    # then it sends this information to the server in a JSON-encoded dictionary with the action type set to "join_room"
    # after sending the request, the method waits for the server response,
    # which is expected to be a message indicating whether the user was successfully added to the room or not
    def join_room(self) :
        room_ID = input("Enter a room ID to join : ")
        room_password = input("Enter the room password to join : ")
        action = {"action" : "join_room", "room_ID" : room_ID, "room_password" : room_password}
        try :
            self.client_sock.send(json.dumps(action).encode('utf-8'))
            join_response = self.client_sock.recv(1024).decode('utf-8')
            join_data = json.loads(join_response)
            print(join_data["message"])
            return json.loads(join_response)
        except (socket.error, ConnectionResetError) as exception :
            print(f"Error joining the room : {exception}")
            self.client_sock.close()
            exit(1)

    # continuously listens for incoming messages from the server in a non-blocking manner
    # operates within a while loop, which keeps running as long as the listener_event is not set
    # sets a timeout of 1 second using self.client_sock.settimeout(1.0)
    # which means the client will attempt to receive data, but will not block indefinitely if no message is received
    def listen_for_messages(self) :
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
            except (socket.error, ConnectionResetError) as exception :
                print(f"Error : {exception}")
                return

    # manages the chatting session
    # starts by clearing the listener_event and launching a listener thread to handle incoming messages
    # the user can then input messages in a loop, if the user types "quit",
    # the method sends a "disconnect" action to the server and prints a message that the user has left the room
    # then sets the listener_event to stop the listener thread and waits for it to finish with join()
    # finally, the method resets the current_room and exits the loop, returning the user to the main menu
    def chat(self) :
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
                action = {"action" : "send_message", "username" : self.username, "message" : message}
                print(f"{self.username} >> {action["message"]}")
                self.client_sock.send(json.dumps(action).encode('utf-8'))

    # controls the main flow of the program, guiding the user through registration or login
    # then provides a command prompt for the user to interact with the chatroom system
    # Registration/Authentication : the user can choose to register (r) or log in (l)
    # Upon successful registration or login (code 200), the username and isAdmin variables are set
    # create : only admins can create new rooms
    # delete : only admins can delete rooms
    # list : view a list of available rooms
    # join : join a room (if successful, the user enters the chatting session)
    # exit : closes the connection and exits the loop
    # permissions : non-admin users are denied access to room creation and deletion with a "Permission Denied" message
    def main(self) :
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
                command = input("\nEnter a command\n\n --list--\n --create--\n --delete--\n --join--\n --exit--\n\n ").lower()
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