import threading
import time

from ankit import transaction_manager
from ansh import deadlock_detector
from ansh import deadlock_event_log
from tanishka import db_wrapper
from tanu import attack_correlator

errors = []


def try_write(txn_id, key, value):
    try:
        transaction_manager.write(txn_id, "accounts", key, value)
    except Exception as e:
        errors.append(str(e))


def test_live_deadlock():
    t1 = transaction_manager.begin("u1")
    t2 = transaction_manager.begin("u2")
    transaction_manager.write(t1, "accounts", 1, 900)
    transaction_manager.write(t2, "accounts", 2, 800)
    a = threading.Thread(target=try_write, args=(t1, 2, 700))
    b = threading.Thread(target=try_write, args=(t2, 1, 600))
    a.start()
    b.start()
    time.sleep(0.5)
    assert deadlock_detector.detect_once()
    a.join(5)
    b.join(5)
    states = [transaction_manager.get_state(t1), transaction_manager.get_state(t2)]
    assert states.count("aborted") == 1
    survivor = t1
    if states[0] == "aborted":
        survivor = t2
    transaction_manager.commit(survivor)
    assert transaction_manager.get_state(survivor) == "committed"
    assert len(deadlock_event_log.get_events()) == 1
    print("PASS test_live_deadlock")


if __name__ == "__main__":
    db_wrapper.reset_accounts()
    deadlock_event_log.reset_events()
    attack_correlator.reset_all()
    test_live_deadlock()
    db_wrapper.reset_accounts()
    deadlock_event_log.reset_events()
    attack_correlator.reset_all()
