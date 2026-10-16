from tanishka import db_wrapper
from tanishka import lost_update_demo


def test_without_locks():
    result = lost_update_demo.run_without_locks()
    assert result["lost"] is True
    assert result["final"] == result["start"] + 100
    print("PASS test_without_locks")


def test_with_locks():
    result = lost_update_demo.run_with_locks()
    assert result["lost"] is False
    assert result["final"] == result["start"] + 200
    print("PASS test_with_locks")


if __name__ == "__main__":
    test_without_locks()
    test_with_locks()
    db_wrapper.reset_accounts()
