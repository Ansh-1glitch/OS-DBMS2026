from tanishka import db_wrapper


def test_read_write():
    db_wrapper.reset_accounts()
    assert db_wrapper.read("accounts", 1) == 1000
    db_wrapper.write("accounts", 1, 500)
    assert db_wrapper.read("accounts", 1) == 500
    db_wrapper.reset_accounts()
    assert db_wrapper.read("accounts", 1) == 1000
    print("PASS test_read_write")


if __name__ == "__main__":
    test_read_write()
