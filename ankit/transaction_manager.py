import threading

from ansh import wal
from tanishka import db_wrapper
from tanishka import lock_manager

transactions = {}
next_id = 1
user_aborts = {}
id_lock = threading.Lock()


def check_active(txn_id):
    if get_state(txn_id) != "active":
        raise Exception("transaction not active")


def begin(user):
    global next_id
    with id_lock:
        txn_id = next_id
        next_id = next_id + 1
        transactions[txn_id] = {"user": user, "state": "active", "writes": 0}
    wal.log_begin(txn_id)
    return txn_id


def read(txn_id, table, key):
    check_active(txn_id)
    lock_manager.acquire(txn_id, table + ":" + str(key), "S")
    return db_wrapper.read(table, key)


def write(txn_id, table, key, value):
    check_active(txn_id)
    lock_manager.acquire(txn_id, table + ":" + str(key), "X")
    old = db_wrapper.read(table, key)
    if old is None:
        raise Exception("row not found")
    wal.log_update(txn_id, table, key, old, value)
    db_wrapper.write(table, key, value)
    transactions[txn_id]["writes"] = transactions[txn_id]["writes"] + 1


def commit(txn_id):
    check_active(txn_id)
    wal.log_commit(txn_id)
    transactions[txn_id]["state"] = "committed"
    lock_manager.release_all(txn_id)


def abort(txn_id):
    if get_state(txn_id) != "active":
        return
    txn = transactions[txn_id]
    txn["state"] = "aborted"
    user = txn["user"]
    user_aborts[user] = user_aborts.get(user, 0) + 1
    lock_manager.mark_aborted(txn_id)
    wal.rollback(txn_id)
    lock_manager.release_all(txn_id)
    print("transaction aborted", txn_id)


def get_user(txn_id):
    if txn_id not in transactions:
        return None
    return transactions[txn_id]["user"]


def get_state(txn_id):
    if txn_id not in transactions:
        return None
    return transactions[txn_id]["state"]


def get_info(txn_id):
    if txn_id not in transactions:
        return None
    txn = transactions[txn_id]
    return {
        "user": txn["user"],
        "state": txn["state"],
        "writes": txn["writes"],
        "locks": lock_manager.count_locks(txn_id),
        "aborts": user_aborts.get(txn["user"], 0),
    }
