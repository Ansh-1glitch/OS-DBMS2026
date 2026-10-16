import threading
import time

from ankit import transaction_manager
from tanishka import db_wrapper
from tanishka import lock_manager


def add_without_lock():
    try:
        balance = db_wrapper.read("accounts", 1)
        time.sleep(0.2)
        db_wrapper.write("accounts", 1, balance + 100)
    except Exception as e:
        print("worker error:", e)


def add_with_lock(user):
    txn_id = None
    try:
        txn_id = transaction_manager.begin(user)
        lock_manager.acquire(txn_id, "accounts:1", "X")
        balance = transaction_manager.read(txn_id, "accounts", 1)
        time.sleep(0.2)
        transaction_manager.write(txn_id, "accounts", 1, balance + 100)
        transaction_manager.commit(txn_id)
    except Exception as e:
        print("worker error:", e)
        if txn_id is not None:
            transaction_manager.abort(txn_id)


def run_threads(target, args_list):
    threads = []
    for args in args_list:
        t = threading.Thread(target=target, args=args)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()


def make_result(start, final):
    expected = start + 200
    return {"start": start, "expected": expected, "final": final, "lost": final != expected}


def run_without_locks():
    db_wrapper.reset_accounts()
    start = db_wrapper.read("accounts", 1)
    run_threads(add_without_lock, [(), ()])
    final = db_wrapper.read("accounts", 1)
    db_wrapper.reset_accounts()
    result = make_result(start, final)
    print("without locks:", result)
    return result


def run_with_locks():
    db_wrapper.reset_accounts()
    start = db_wrapper.read("accounts", 1)
    run_threads(add_with_lock, [("demo1",), ("demo2",)])
    final = db_wrapper.read("accounts", 1)
    db_wrapper.reset_accounts()
    result = make_result(start, final)
    print("with locks:", result)
    return result
