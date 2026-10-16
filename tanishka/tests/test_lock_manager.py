import threading
import time

from tanishka import lock_manager

events = []


def find_lock(resource):
    for item in lock_manager.get_locks():
        if item["resource"] == resource:
            return item
    return None


def grab(txn_id, resource, mode):
    try:
        lock_manager.acquire(txn_id, resource, mode)
        events.append(txn_id)
        time.sleep(0.1)
        lock_manager.release_all(txn_id)
    except Exception as e:
        events.append(str(e))


def start(txn_id, resource, mode):
    t = threading.Thread(target=grab, args=(txn_id, resource, mode))
    t.start()
    time.sleep(0.2)
    return t


def test_shared_locks():
    lock_manager.acquire(1, "accounts:1", "S")
    lock_manager.acquire(2, "accounts:1", "S")
    info = find_lock("accounts:1")
    assert info["mode"] == "S"
    assert info["holders"] == [1, 2]
    lock_manager.release_all(1)
    lock_manager.release_all(2)
    assert find_lock("accounts:1") is None
    print("PASS test_shared_locks")


def test_x_waits_for_s():
    del events[:]
    lock_manager.acquire(10, "accounts:2", "S")
    t = start(11, "accounts:2", "X")
    assert events == []
    assert find_lock("accounts:2")["waiting"] == [11]
    lock_manager.release_all(10)
    t.join(3)
    assert events == [11]
    print("PASS test_x_waits_for_s")


def test_upgrade():
    lock_manager.acquire(20, "accounts:3", "S")
    lock_manager.acquire(20, "accounts:3", "X")
    info = find_lock("accounts:3")
    assert info["mode"] == "X"
    assert info["holders"] == [20]
    assert lock_manager.count_locks(20) == 1
    lock_manager.release_all(20)
    assert lock_manager.count_locks(20) == 0
    print("PASS test_upgrade")


def test_fifo():
    del events[:]
    lock_manager.acquire(30, "accounts:4", "X")
    t1 = start(31, "accounts:4", "X")
    t2 = start(32, "accounts:4", "X")
    assert find_lock("accounts:4")["waiting"] == [31, 32]
    lock_manager.release_all(30)
    t1.join(3)
    t2.join(3)
    assert events == [31, 32]
    print("PASS test_fifo")


def test_abort_wakes_waiter():
    del events[:]
    lock_manager.acquire(40, "accounts:5", "X")
    t = start(41, "accounts:5", "X")
    lock_manager.mark_aborted(41)
    t.join(3)
    assert events == ["transaction aborted"]
    assert find_lock("accounts:5")["waiting"] == []
    lock_manager.release_all(41)
    lock_manager.release_all(40)
    assert find_lock("accounts:5") is None
    print("PASS test_abort_wakes_waiter")


def run_all():
    test_shared_locks()
    test_x_waits_for_s()
    test_upgrade()
    test_fifo()
    test_abort_wakes_waiter()
    print("all lock manager tests passed")


if __name__ == "__main__":
    run_all()
