drop table if exists users;

create table users (
user_ID int auto_increment primary key,
username varchar(60) not null,
password varchar(60) not null
);

insert into users (username, password)
values ("admin", "admin123");

drop table if exists rooms;

create table rooms (
room_ID int auto_increment primary key,
room_name varchar(60) not null,
room_description varchar(240),
room_password varchar(60),
created_at timestamp default current_timestamp
);

insert into rooms (room_name, room_description, room_password) values
("test", "Welcome to our Chatroom!", "test5");