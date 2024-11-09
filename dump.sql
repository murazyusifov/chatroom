CREATE DATABASE chatroom_db;

USE chatroom_db;

CREATE TABLE rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_name VARCHAR(100) NOT NULL,
    room_password VARCHAR(100),
    room_type ENUM('public', 'private') NOT NULL
);

CREATE TABLE users (
    username VARCHAR(50) PRIMARY KEY,
    password VARCHAR(100) NOT NULL,
    role_type ENUM('admin', 'user') NOT NULL
);

insert into users(username, password, role_type) values("admin","admin","admin");
