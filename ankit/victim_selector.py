from ankit import transaction_manager

LOCK_WEIGHT = 1
WORK_WEIGHT = 1
ABORT_WEIGHT = 2


def get_cost(info):
    return LOCK_WEIGHT * info["locks"] + WORK_WEIGHT * info["writes"] + ABORT_WEIGHT * info["aborts"]


def select_victim(cycle):
    victim = None
    best = None
    for txn_id in cycle:
        info = transaction_manager.get_info(txn_id)
        if info is None or info["state"] != "active":
            continue
        cost = get_cost(info)
        if victim is None or cost < best or (cost == best and txn_id > victim):
            victim = txn_id
            best = cost
    return victim
