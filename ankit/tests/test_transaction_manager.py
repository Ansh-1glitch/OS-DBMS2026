from ankit import transaction_manager
from tanishka import db_wrapper


def test_commit():
    txn_id = transaction_manager.begin("alice")
    transaction_manager.write(txn_id, "accounts", 1, 900)
    transaction_manager.commit(txn_id)
    assert db_wrapper.read("accounts", 1) == 900
    print("PASS test_commit")


def test_abort():
    txn_id = transaction_manager.begin("bob")
    transaction_manager.write(txn_id, "accounts", 2, 700)
    transaction_manager.abort(txn_id)
    assert db_wrapper.read("accounts", 2) == 1000
    print("PASS test_abort")


def test_transfer():
    txn_id = transaction_manager.begin("carol")
    a = transaction_manager.read(txn_id, "accounts", 3)
    b = transaction_manager.read(txn_id, "accounts", 4)
    transaction_manager.write(txn_id, "accounts", 3, a - 100)
    transaction_manager.write(txn_id, "accounts", 4, b + 100)
    transaction_manager.commit(txn_id)
    assert db_wrapper.read("accounts", 3) == 900
    assert db_wrapper.read("accounts", 4) == 1100
    print("PASS test_transfer")


def test_read_after_commit():
    txn_id = transaction_manager.begin("dave")
    transaction_manager.commit(txn_id)
    failed = False
    try:
        transaction_manager.read(txn_id, "accounts", 5)
    except Exception:
        failed = True
    assert failed
    print("PASS test_read_after_commit")


if __name__ == "__main__":
    db_wrapper.reset_accounts()
    test_commit()
    test_abort()
    test_transfer()
    test_read_after_commit()
    db_wrapper.reset_accounts()
