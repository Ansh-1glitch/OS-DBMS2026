import mysql.connector

from shared import config


def get_connection():
    conn = mysql.connector.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
    )
    conn.autocommit = True
    return conn


def read(table, key):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT balance FROM " + table + " WHERE id = %s", (key,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        return None
    return row[0]


def write(table, key, value):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE " + table + " SET balance = %s WHERE id = %s", (value, key))
    cur.close()
    conn.close()


def insert(table, values):
    columns = []
    marks = []
    data = []
    for column in values:
        columns.append(column)
        marks.append("%s")
        data.append(values[column])
    sql = "INSERT INTO " + table + " (" + ", ".join(columns) + ") VALUES (" + ", ".join(marks) + ")"
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, tuple(data))
    new_id = cur.lastrowid
    cur.close()
    conn.close()
    return new_id


def select_all(table):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM " + table)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def find(table, column, value):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM " + table + " WHERE " + column + " = %s", (value,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def reset_accounts():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE accounts SET balance = %s", (1000,))
    cur.close()
    conn.close()
