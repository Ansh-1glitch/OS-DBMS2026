# OSDBMS-Sentinel

A DBMS project with row-level Strict 2PL locking, deadlock detection, write-ahead logging and a security layer.
MySQL is used for storage only.

## Setup

    pip install -r requirements.txt
    mysql -u root < tanishka/schema.sql

## Run

    python run_demo.py
