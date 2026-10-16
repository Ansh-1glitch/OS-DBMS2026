import threading

from ansh import wait_for_graph

lock_table = {}
held_by = {}
aborted = []
mutex = threading.Lock()
cond = threading.Condition(mutex)


def get_entry(resource):
    if resource not in lock_table:
        lock_table[resource] = {"mode": None, "holders": [], "queue": []}
    return lock_table[resource]


def drop_if_empty(resource):
    entry = lock_table[resource]
    if len(entry["holders"]) == 0 and len(entry["queue"]) == 0:
        del lock_table[resource]


def remove_from_queue(entry, txn_id):
    new_queue = []
    for item in entry["queue"]:
        if item[0] != txn_id:
            new_queue.append(item)
    entry["queue"] = new_queue


def in_queue(entry, txn_id):
    for item in entry["queue"]:
        if item[0] == txn_id:
            return True
    return False


def ahead_of(entry, txn_id):
    ahead = []
    for item in entry["queue"]:
        if item[0] == txn_id:
            return ahead
        ahead.append(item[0])
    return ahead


def can_grant(entry, txn_id, mode):
    holders = entry["holders"]
    if txn_id in holders and entry["mode"] == "X":
        return True
    if txn_id in holders and mode == "S":
        return True
    ahead = ahead_of(entry, txn_id)
    if mode == "S":
        if len(holders) == 0 or entry["mode"] == "S":
            return len(ahead) == 0
        return False
    if len(holders) == 1 and holders[0] == txn_id:
        return True
    return len(holders) == 0 and len(ahead) == 0


def grant(entry, resource, txn_id, mode):
    if mode == "X" or len(entry["holders"]) == 0:
        entry["mode"] = mode
    if txn_id not in entry["holders"]:
        entry["holders"].append(txn_id)
    if txn_id not in held_by:
        held_by[txn_id] = []
    if resource not in held_by[txn_id]:
        held_by[txn_id].append(resource)
    remove_from_queue(entry, txn_id)
    wait_for_graph.remove_edges(txn_id)


def add_wait_edges(entry, txn_id):
    for other in entry["holders"]:
        if other != txn_id:
            wait_for_graph.add_edge(txn_id, other)
    for other in ahead_of(entry, txn_id):
        if other != txn_id:
            wait_for_graph.add_edge(txn_id, other)


def acquire(txn_id, resource, mode):
    with cond:
        while True:
            entry = get_entry(resource)
            if txn_id in aborted:
                remove_from_queue(entry, txn_id)
                drop_if_empty(resource)
                wait_for_graph.remove_edges(txn_id)
                raise Exception("transaction aborted")
            if can_grant(entry, txn_id, mode):
                grant(entry, resource, txn_id, mode)
                return
            if not in_queue(entry, txn_id):
                entry["queue"].append((txn_id, mode))
            add_wait_edges(entry, txn_id)
            cond.wait(1)


def release_all(txn_id):
    with cond:
        for resource in list(lock_table.keys()):
            entry = lock_table[resource]
            if txn_id in entry["holders"]:
                entry["holders"].remove(txn_id)
            if len(entry["holders"]) == 0:
                entry["mode"] = None
            remove_from_queue(entry, txn_id)
            drop_if_empty(resource)
        if txn_id in held_by:
            del held_by[txn_id]
        wait_for_graph.remove_node(txn_id)
        cond.notify_all()


def mark_aborted(txn_id):
    with cond:
        if txn_id not in aborted:
            aborted.append(txn_id)
        cond.notify_all()


def count_locks(txn_id):
    with cond:
        if txn_id not in held_by:
            return 0
        return len(held_by[txn_id])


def get_locks():
    result = []
    with cond:
        for resource in lock_table:
            entry = lock_table[resource]
            waiting = []
            for item in entry["queue"]:
                waiting.append(item[0])
            result.append({
                "resource": resource,
                "mode": entry["mode"],
                "holders": list(entry["holders"]),
                "waiting": waiting,
            })
    return result
