import threading
import time

from shared import config
from tanishka import db_wrapper

request_times = {}
rate_lock = threading.Lock()


def check_rate(user):
    now = time.time()
    with rate_lock:
        kept = []
        for t in request_times.get(user, []):
            if t > now - 60:
                kept.append(t)
        request_times[user] = kept
        if len(kept) >= config.RATE_LIMIT_PER_MINUTE:
            return False
        kept.append(now)
        return True


def log_audit(user, action, status):
    try:
        db_wrapper.insert("audit_log", {"username": user, "action": action, "status": status})
    except Exception:
        print("could not save audit")


def reset_rates():
    with rate_lock:
        request_times.clear()
