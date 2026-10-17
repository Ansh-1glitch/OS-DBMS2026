import time

from shared import config
from tanu import attack_correlator
from tanu import rate_limiter
from tanu import security_gateway

stamp = str(int(time.time()))
name = "user" + stamp
reader = "reader" + stamp


def test_add_user():
    assert security_gateway.add_user(name, "secret1", "user")
    assert not security_gateway.add_user(name, "other", "user")
    print("PASS test_add_user")


def test_login():
    assert security_gateway.login(name, "secret1") == "user"
    assert security_gateway.login(name, "wrong") is None
    print("PASS test_login")


def test_safe_input():
    assert not security_gateway.is_safe_input("' OR 1=1 --")
    assert security_gateway.is_safe_input("alice")
    print("PASS test_safe_input")


def test_readonly():
    security_gateway.add_user(reader, "pass", "readonly")
    assert security_gateway.check_request(reader, "write", "1") == (False, "not allowed")
    assert security_gateway.check_request(reader, "read", "1") == (True, "ok")
    print("PASS test_readonly")


def test_unknown_user():
    assert security_gateway.check_request("nobody" + stamp, "read", "1") == (False, "unknown user")
    print("PASS test_unknown_user")


def test_quarantined():
    for i in range(config.ATTACK_LIMIT):
        attack_correlator.record_deadlock([name], 100 + i)
    assert security_gateway.check_request(name, "read", "1") == (False, "quarantined")
    print("PASS test_quarantined")


if __name__ == "__main__":
    attack_correlator.reset_all()
    rate_limiter.reset_rates()
    test_add_user()
    test_login()
    test_safe_input()
    test_readonly()
    test_unknown_user()
    test_quarantined()
    attack_correlator.reset_all()
