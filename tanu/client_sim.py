import json
import threading
import time
import urllib.error
import urllib.request

from shared import config
from tanishka import db_wrapper
from tanu import security_gateway

results = {}


def read_reply(status, raw):
    try:
        reply = json.loads(raw.decode("utf-8"))
    except Exception:
        return 0, {"error": "reply is not json"}
    if not isinstance(reply, dict):
        reply = {"data": reply}
    return status, reply


def post_url(url, data):
    try:
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=30) as res:
            return read_reply(res.status, res.read())
    except urllib.error.HTTPError as e:
        return read_reply(e.code, e.read())
    except Exception as e:
        return 0, {"error": "server not reachable: " + str(e)}


def post(path, data):
    url = "http://" + config.API_HOST + ":" + str(config.API_PORT) + path
    return post_url(url, data)


def setup_users():
    for user in ["alice", "bob", "mallory"]:
        security_gateway.add_user(user, "pass123", "user")


def begin_txn(user):
    status, reply = post("/api/begin", {"user": user})
    if status != 200:
        print(user, "begin failed", status, reply.get("error"))
        return None, status
    return reply["txn_id"], status


def abort_txn(txn_id):
    if txn_id is not None:
        post("/api/abort", {"txn_id": txn_id})


def write_row(txn_id, key, value):
    return post("/api/write", {"txn_id": txn_id, "table": "accounts", "key": key, "value": value})


def step_failed(user, txn_id, step, reply):
    print(user, step, "failed:", reply.get("error"))
    abort_txn(txn_id)


def normal_round(user, key):
    txn_id, status = begin_txn(user)
    print(user, "begin", status)
    if txn_id is None:
        return
    status, reply = post("/api/read", {"txn_id": txn_id, "table": "accounts", "key": key})
    print(user, "read", status)
    if status != 200:
        return step_failed(user, txn_id, "read", reply)
    status, reply = write_row(txn_id, key, reply["value"] + 1)
    print(user, "write", status)
    if status != 200:
        return step_failed(user, txn_id, "write", reply)
    status, reply = post("/api/commit", {"txn_id": txn_id})
    print(user, "commit", status)
    if status != 200:
        step_failed(user, txn_id, "commit", reply)


def normal_user(user, rounds, key):
    try:
        status, reply = post("/api/login", {"username": user, "password": "pass123"})
        print(user, "login", status)
        for i in range(rounds):
            normal_round(user, key)
            time.sleep(0.5)
    except Exception as e:
        print(user, "error:", e)


def run_normal(rounds):
    a = threading.Thread(target=normal_user, args=("alice", rounds, 3))
    b = threading.Thread(target=normal_user, args=("bob", rounds, 4))
    a.start()
    b.start()
    a.join()
    b.join()


def write_worker(name, txn_id, key):
    try:
        results[name] = write_row(txn_id, key, 1000)
    except Exception as e:
        print(name, "error:", e)
        results[name] = (0, {"error": str(e)})


def run_crossed(a_txn, b_txn):
    results["a"] = (0, {"error": "no reply"})
    results["b"] = (0, {"error": "no reply"})
    a = threading.Thread(target=write_worker, args=("a", a_txn, 2))
    b = threading.Thread(target=write_worker, args=("b", b_txn, 1))
    a.start()
    b.start()
    a.join(40)
    b.join(40)
    return results["a"][0], results["b"][0]


def finish_round(a_txn, b_txn, a_status, b_status):
    if a_status == 200:
        post("/api/commit", {"txn_id": a_txn})
    if b_status == 200:
        post("/api/commit", {"txn_id": b_txn})
    abort_txn(a_txn)
    abort_txn(b_txn)
    if a_status != 200:
        print("txn", a_txn, "was aborted:", results["a"][1].get("error"))
    if b_status != 200:
        print("txn", b_txn, "was aborted:", results["b"][1].get("error"))


def deadlock_round(user_a, user_b):
    a_txn, a_status = begin_txn(user_a)
    b_txn, b_status = begin_txn(user_b)
    if a_txn is None or b_txn is None:
        abort_txn(a_txn)
        abort_txn(b_txn)
        return {"a_status": a_status, "b_status": b_status}
    a_status = write_row(a_txn, 1, 1000)[0]
    b_status = write_row(b_txn, 2, 1000)[0]
    if a_status != 200 or b_status != 200:
        print("first writes failed", a_status, b_status)
        abort_txn(a_txn)
        abort_txn(b_txn)
        return {"a_status": a_status, "b_status": b_status}
    a_status, b_status = run_crossed(a_txn, b_txn)
    finish_round(a_txn, b_txn, a_status, b_status)
    return {"a_status": a_status, "b_status": b_status}


def begin_status(user):
    status, reply = post("/api/begin", {"user": user})
    if status == 200:
        abort_txn(reply["txn_id"])
    return status


def hit_rate_limit(reply):
    return reply["a_status"] == 429 or reply["b_status"] == 429


def attacker(user, rounds):
    reply = deadlock_round("alice", user)
    count = 1
    while count < rounds and not hit_rate_limit(reply):
        if begin_status(user) == 403:
            break
        reply = deadlock_round(user, user)
        count = count + 1
    blocked = begin_status(user) == 403
    alice_ok = begin_status("alice") == 200
    print("rounds run:", count)
    print(user, "quarantined:", blocked)
    print("alice can still begin:", alice_ok)
    return {"rounds": count, "mallory_quarantined": blocked, "alice_ok": alice_ok}


def run_simulation(rounds):
    db_wrapper.reset_accounts()
    setup_users()
    run_normal(rounds)
    result = attacker("mallory", config.ATTACK_LIMIT + 3)
    db_wrapper.reset_accounts()
    return result


if __name__ == "__main__":
    run_simulation(4)
