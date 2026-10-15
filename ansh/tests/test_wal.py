from ansh import wal
from tanishka import db_wrapper


def test_rollback():
    db_wrapper.reset_accounts()
    wal.log_begin(1001)
    old = db_wrapper.read("accounts", 1)
    wal.log_update(1001, "accounts", 1, old, 500)
    db_wrapper.write("accounts", 1, 500)
    wal.rollback(1001)
    assert db_wrapper.read("accounts", 1) == 1000
    print("PASS test_rollback")


def test_recover():
    db_wrapper.reset_accounts()
    wal.log_begin(1002)
    old = db_wrapper.read("accounts", 3)
    wal.log_update(1002, "accounts", 3, old, 555)
    db_wrapper.write("accounts", 3, 555)
    wal.recover()
    assert db_wrapper.read("accounts", 3) == 1000
    print("PASS test_recover")


if __name__ == "__main__":
    test_rollback()
    test_recover()
    db_wrapper.reset_accounts()
