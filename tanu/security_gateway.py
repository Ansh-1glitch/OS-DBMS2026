import hashlib
import hmac
import os

from tanishka import db_wrapper
from tanu import attack_correlator
from tanu import rate_limiter

bad_words = ["'", '"', "--", ";", "/*", "*/", "union select", "drop table", "or 1=1", "xp_"]
roles = ["admin", "user", "readonly"]


def make_hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()


def add_user(username, password, role):
    if role not in roles:
        return False
    if len(db_wrapper.find("users", "username", username)) > 0:
        return False
    salt = os.urandom(8).hex()
    db_wrapper.insert("users", {
        "username": username,
        "password_hash": make_hash(password, salt),
        "salt": salt,
        "role": role,
    })
    return True


def login(username, password):
    rows = db_wrapper.find("users", "username", username)
    if len(rows) == 0:
        rate_limiter.log_audit(username, "login", "failed")
        return None
    row = rows[0]
    if hmac.compare_digest(make_hash(password, row["salt"]), row["password_hash"]):
        rate_limiter.log_audit(username, "login", "ok")
        return row["role"]
    rate_limiter.log_audit(username, "login", "failed")
    return None


def is_safe_input(text):
    text = str(text).lower()
    for word in bad_words:
        if word in text:
            return False
    return True


def find_reason(user, action, text):
    if attack_correlator.is_quarantined(user):
        return "quarantined"
    if not rate_limiter.check_rate(user):
        return "rate limit"
    if not is_safe_input(text):
        return "unsafe input"
    rows = db_wrapper.find("users", "username", user)
    if len(rows) == 0:
        return "unknown user"
    if rows[0]["role"] == "readonly" and (action == "write" or action == "transfer"):
        return "not allowed"
    return "ok"


def check_request(user, action, text):
    reason = find_reason(user, action, text)
    rate_limiter.log_audit(user, action, reason)
    return (reason == "ok", reason)
