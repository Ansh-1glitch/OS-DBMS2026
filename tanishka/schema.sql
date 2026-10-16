CREATE DATABASE IF NOT EXISTS sentinel;
USE sentinel;

CREATE TABLE IF NOT EXISTS accounts (
    id INT PRIMARY KEY,
    owner VARCHAR(50),
    balance INT
);

CREATE TABLE IF NOT EXISTS wal_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    txn_id INT,
    record_type VARCHAR(10),
    table_name VARCHAR(50),
    row_key INT,
    old_value INT,
    new_value INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS deadlock_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cycle VARCHAR(200),
    victim INT,
    users VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    password_hash VARCHAR(100),
    salt VARCHAR(40),
    role VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50),
    action VARCHAR(50),
    status VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50),
    reason VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT IGNORE INTO accounts (id, owner, balance) VALUES
    (1, 'alice', 1000),
    (2, 'bob', 1000),
    (3, 'carol', 1000),
    (4, 'dave', 1000),
    (5, 'erin', 1000);
