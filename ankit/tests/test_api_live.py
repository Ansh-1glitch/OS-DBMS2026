import time

from ankit import api
from tanishka import db_wrapper
from tanu import attack_correlator
from tanu import rate_limiter
from tanu import security_gateway

client = api.app.test_client()
name = "api" + str(int(time.time()))


def post(path, body):
    return client.post(path, json=body)


def begin():
    return post("/api/begin", {"user": name}).get_json()["txn_id"]


def read_balance(key):
    txn_id = begin()
    value = post("/api/read", {"txn_id": txn_id, "table": "accounts", "key": key}).get_json()["value"]
    post("/api/commit", {"txn_id": txn_id})
    return value


def test_login():
    res = post("/api/login", {"username": name, "password": "pass123"})
    assert res.status_code == 200
    assert res.get_json() == {"role": "user"}
    res = post("/api/login", {"username": name, "password": "wrong"})
    assert res.status_code == 401
    print("PASS test_login")


def test_write_commit():
    txn_id = begin()
    res = post("/api/write", {"txn_id": txn_id, "table": "accounts", "key": 1, "value": 900})
    assert res.status_code == 200
    assert post("/api/commit", {"txn_id": txn_id}).status_code == 200
    assert read_balance(1) == 900
    print("PASS test_write_commit")


def test_transfer():
    txn_id = begin()
    res = post("/api/transfer", {"txn_id": txn_id, "from_key": 3, "to_key": 4, "amount": 100})
    assert res.status_code == 200
    assert post("/api/commit", {"txn_id": txn_id}).status_code == 200
    assert read_balance(3) == 900
    assert read_balance(4) == 1100
    print("PASS test_transfer")


def test_unsafe_table():
    txn_id = begin()
    res = post("/api/write", {"txn_id": txn_id, "table": "accounts'", "key": 1, "value": 5})
    assert res.status_code == 400
    assert res.get_json() == {"error": "unsafe input"}
    post("/api/abort", {"txn_id": txn_id})
    print("PASS test_unsafe_table")


def test_demo_with_locks():
    res = client.post("/api/demo/with_locks")
    assert res.status_code == 200
    assert res.get_json()["lost"] is False
    print("PASS test_demo_with_locks")


def clean():
    db_wrapper.reset_accounts()
    attack_correlator.reset_all()
    rate_limiter.reset_rates()


if __name__ == "__main__":
    clean()
    security_gateway.add_user(name, "pass123", "user")
    test_login()
    test_write_commit()
    test_transfer()
    test_unsafe_table()
    test_demo_with_locks()
    clean()
