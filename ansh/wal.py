import threading

from tanishka import db_wrapper

log_list = []
log_lock = threading.Lock()


def add_record(txn_id, record_type, table, key, old, new):
    record = {"txn_id": txn_id, "type": record_type, "table": table, "key": key, "old": old, "new": new}
    with log_lock:
        log_list.append(record)
    db_wrapper.insert("wal_log", {
        "txn_id": txn_id,
        "record_type": record_type,
        "table_name": table,
        "row_key": key,
        "old_value": old,
        "new_value": new,
    })


def log_begin(txn_id):
    add_record(txn_id, "BEGIN", None, None, None, None)


def log_update(txn_id, table, key, old, new):
    add_record(txn_id, "UPDATE", table, key, old, new)


def log_commit(txn_id):
    add_record(txn_id, "COMMIT", None, None, None, None)


def log_abort(txn_id):
    add_record(txn_id, "ABORT", None, None, None, None)


def rollback(txn_id):
    with log_lock:
        records = list(log_list)
    count = 0
    i = len(records) - 1
    while i >= 0:
        record = records[i]
        if record["txn_id"] == txn_id and record["type"] == "UPDATE":
            db_wrapper.write(record["table"], record["key"], record["old"])
            count = count + 1
        i = i - 1
    log_abort(txn_id)
    print("rollback txn", txn_id, "undid", count, "updates")


def get_id(row):
    return row["id"]


def read_log():
    rows = sorted(db_wrapper.select_all("wal_log"), key=get_id)
    state = {}
    updates = {}
    for row in rows:
        txn_id = row["txn_id"]
        kind = row["record_type"]
        if kind == "BEGIN":
            state[txn_id] = "active"
            updates[txn_id] = []
        elif kind == "UPDATE":
            if txn_id not in updates:
                updates[txn_id] = []
            updates[txn_id].append((row["table_name"], row["row_key"], row["old_value"]))
        elif kind == "COMMIT":
            state[txn_id] = "committed"
        elif kind == "ABORT":
            state[txn_id] = "aborted"
    return state, updates


def undo(txn_id, items):
    i = len(items) - 1
    while i >= 0:
        item = items[i]
        db_wrapper.write(item[0], item[1], item[2])
        i = i - 1
    log_abort(txn_id)


def recover():
    state, updates = read_log()
    undone = []
    for txn_id in state:
        if state[txn_id] == "active":
            undo(txn_id, updates[txn_id])
            undone.append(txn_id)
    if len(undone) == 0:
        print("recover: nothing to undo")
    else:
        print("recover: undid transactions", undone)
