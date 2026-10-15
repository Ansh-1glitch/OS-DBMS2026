CREATE DATABASE IF NOT EXISTS sentinel;
USE sentinel;

CREATE TABLE IF NOT EXISTS accounts (
    id INT PRIMARY KEY,
    owner VARCHAR(50),
    balance INT
);
