from ankit import transaction_manager
from ankit import victim_selector
from tanishka import lock_manager


def add_txn(txn_id, user, state, writes):
    transaction_manager.transactions[txn_id] = {"user": user, "state": state, "writes": writes}


def clean():
    for txn_id in [9001, 9002, 9003]:
        lock_manager.release_all(txn_id)
        if txn_id in transaction_manager.transactions:
            del transaction_manager.transactions[txn_id]
    transaction_manager.user_aborts.clear()


def test_cheapest_chosen():
    add_txn(9001, "alice", "active", 3)
    add_txn(9002, "bob", "active", 0)
    lock_manager.acquire(9001, "accounts:1", "X")
    lock_manager.acquire(9001, "accounts:2", "X")
    lock_manager.acquire(9002, "accounts:3", "X")
    assert victim_selector.select_victim([9001, 9002]) == 9002
    clean()
    print("PASS test_cheapest_chosen")


def test_many_aborts_protected():
    add_txn(9001, "alice", "active", 1)
    add_txn(9002, "bob", "active", 0)
    lock_manager.acquire(9001, "accounts:1", "X")
    lock_manager.acquire(9002, "accounts:2", "X")
    transaction_manager.user_aborts["bob"] = 3
    assert victim_selector.select_victim([9001, 9002]) == 9001
    clean()
    print("PASS test_many_aborts_protected")


def test_tie_picks_younger():
    add_txn(9001, "alice", "active", 1)
    add_txn(9002, "bob", "active", 1)
    lock_manager.acquire(9001, "accounts:1", "X")
    lock_manager.acquire(9002, "accounts:2", "X")
    assert victim_selector.select_victim([9002, 9001]) == 9002
    clean()
    print("PASS test_tie_picks_younger")


def test_none_when_nothing_active():
    assert victim_selector.select_victim([]) is None
    add_txn(9001, "alice", "committed", 0)
    add_txn(9003, "carol", "aborted", 0)
    assert victim_selector.select_victim([9001, 9003]) is None
    assert victim_selector.select_victim([9001, 9002, 9003]) is None
    clean()
    print("PASS test_none_when_nothing_active")


def run_all():
    test_cheapest_chosen()
    test_many_aborts_protected()
    test_tie_picks_younger()
    test_none_when_nothing_active()
    print("all victim selector tests passed")


if __name__ == "__main__":
    run_all()
