DROP DATABASE IF EXISTS picture_classification;
CREATE DATABASE picture_classification;
USE picture_classification;

-- DATABASE DEFINITION

CREATE TABLE project (
    project_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(100) NOT NULL,
    date DATE DEFAULT (CURRENT_DATE) NOT NULL
);

CREATE TABLE location (
    location_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    coordinates VARCHAR(50) NOT NULL,
    project_id INT NOT NULL
);

CREATE TABLE album (
    album_id INT AUTO_INCREMENT PRIMARY KEY, 
    location_id INT NOT NULL,
    name VARCHAR(50) UNIQUE NOT NULL,
    date DATE NOT NULL
);

CREATE TABLE picture (
    picture_id CHAR(64) PRIMARY KEY,
    path VARCHAR(255) NOT NULL,
    date DATE NOT NULL DEFAULT (CURRENT_DATE),
    album_id INT NOT NULL
);

CREATE TABLE category (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50)
);

CREATE TABLE tag (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    category_id INT
);

CREATE TABLE user (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(50) UNIQUE NOT NULL,
    password CHAR(60) NOT NULL,
    confirmed_on DATETIME DEFAULT NULL
);

CREATE TABLE rating (
    rating_id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    date DATE NOT NULL DEFAULT (CURRENT_DATE),
    score DECIMAL(5,2) NOT NULL,
    picture_id CHAR(64) NOT NULL, 
    tag_id INT,
    user_id INT
);

CREATE TABLE audit (
    audit_id INT AUTO_INCREMENT NOT NULL PRIMARY KEY,
    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    type ENUM('UPDATE', 'DELETE', 'CREATE', 'REQUEST', 'OTHERS') NOT NULL,
    request TEXT NOT NULL,
    message TEXT NOT NULL,
    status ENUM('success', 'error') NOT NULL,
    user_id INT NOT NULL,
    entity ENUM('project', 'location', 'album', 'picture', 'category', 'tag', 'user', 'rating') NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);

-- INSERT DEFAULT VALUES

INSERT INTO 
    category(name)
VALUES ("Not defined") ;

INSERT INTO tag(name, category_id)
        VALUES("Not defined", 1);

-- DEFAULT CONSTRAINTS

ALTER TABLE 
    location ADD FOREIGN KEY (project_id) REFERENCES project(project_id) ON DELETE CASCADE ;

ALTER TABLE 
    album ADD FOREIGN KEY (location_id) REFERENCES location(location_id) ON DELETE CASCADE;

ALTER TABLE 
    picture ADD FOREIGN KEY (album_id) REFERENCES album(album_id) ON DELETE CASCADE;

ALTER TABLE 
    tag ADD FOREIGN KEY (category_id) REFERENCES category(category_id) ON DELETE CASCADE;

ALTER TABLE
    rating ADD FOREIGN KEY(picture_id) REFERENCES picture(picture_id) ON DELETE CASCADE
    , ADD FOREIGN KEY(user_id) REFERENCES user(user_id) ON DELETE CASCADE
    , ADD FOREIGN KEY(tag_id) REFERENCES tag(tag_id) ON DELETE CASCADE; 