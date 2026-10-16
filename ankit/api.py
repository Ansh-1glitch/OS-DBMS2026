import os

from flask import Flask, jsonify, request

from ankit import transaction_manager
from ansh import deadlock_detector
from ansh import deadlock_event_log
from shared import config
from tanishka import lock_manager
from tanishka import lost_update_demo
from tanu import attack_correlator
from tanu import security_gateway

app = Flask(__name__)
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
page_path = os.path.join(root, "tanishka", "dashboard", "index.html")
tables = ["accounts"]
reason_status = {
    "quarantined": 403,
    "rate limit": 429,
    "unsafe input": 400,
    "unknown user": 401,
    "not allowed": 403,
}
bad_input = (KeyError, ValueError, TypeError)


def error_reply(message, status):
    return jsonify({"error": message}), status


def get_body():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise KeyError("body")
    return body


def make_text(parts):
    words = []
    for part in parts:
        words.append(str(part))
    return " ".join(words)


def check_user(txn_id, action, parts, table):
    user = transaction_manager.get_user(txn_id)
    if user is None:
        return "transaction not active", 400
    allowed, reason = security_gateway.check_request(user, action, make_text(parts))
    if not allowed:
        return reason, reason_status.get(reason, 400)
    if table not in tables:
        return "unknown table", 400
    return None, 200


def home():
    with open(page_path, "r", encoding="utf-8") as f:
        text = f.read()
    return text, 200, {"Content-Type": "text/html; charset=utf-8"}


def locks_route():
    try:
        return jsonify(lock_manager.get_locks())
    except Exception as e:
        return error_reply(str(e), 400)


def graph_route():
    try:
        graph = deadlock_detector.get_wait_graph()
        result = {}
        for waiter in graph:
            result[str(waiter)] = graph[waiter]
        return jsonify(result)
    except Exception as e:
        return error_reply(str(e), 400)


def deadlocks_route():
    try:
        return jsonify(deadlock_event_log.get_events())
    except Exception as e:
        return error_reply(str(e), 400)


def alerts_route():
    try:
        return jsonify(attack_correlator.get_alerts())
    except Exception as e:
        return error_reply(str(e), 400)


def demo_without_route():
    try:
        return jsonify(lost_update_demo.run_without_locks())
    except Exception as e:
        return error_reply(str(e), 400)


def demo_with_route():
    try:
        return jsonify(lost_update_demo.run_with_locks())
    except Exception as e:
        return error_reply(str(e), 400)


def login_route():
    try:
        body = get_body()
        role = security_gateway.login(body["username"], body["password"])
        if role is None:
            return error_reply("login failed", 401)
        return jsonify({"role": role})
    except bad_input:
        return error_reply("bad request", 400)
    except Exception as e:
        return error_reply(str(e), 400)


def begin_route():
    try:
        user = get_body()["user"]
        if attack_correlator.is_quarantined(user):
            return error_reply("quarantined", 403)
        return jsonify({"txn_id": transaction_manager.begin(user)})
    except bad_input:
        return error_reply("bad request", 400)
    except Exception as e:
        return error_reply(str(e), 400)


def read_route():
    try:
        body = get_body()
        txn_id = int(body["txn_id"])
        table = body["table"]
        key = int(body["key"])
        problem, status = check_user(txn_id, "read", [table, key], table)
        if problem is not None:
            return error_reply(problem, status)
        return jsonify({"value": transaction_manager.read(txn_id, table, key)})
    except bad_input:
        return error_reply("bad request", 400)
    except Exception as e:
        return error_reply(str(e), 400)


def write_route():
    try:
        body = get_body()
        txn_id = int(body["txn_id"])
        table = body["table"]
        key = int(body["key"])
        value = int(body["value"])
        problem, status = check_user(txn_id, "write", [table, key, value], table)
        if problem is not None:
            return error_reply(problem, status)
        transaction_manager.write(txn_id, table, key, value)
        return jsonify({"ok": True})
    except bad_input:
        return error_reply("bad request", 400)
    except Exception as e:
        return error_reply(str(e), 400)


def do_transfer(txn_id, from_key, to_key, amount):
    a = transaction_manager.read(txn_id, "accounts", from_key)
    b = transaction_manager.read(txn_id, "accounts", to_key)
    transaction_manager.write(txn_id, "accounts", from_key, a - amount)
    transaction_manager.write(txn_id, "accounts", to_key, b + amount)


def transfer_route():
    try:
        body = get_body()
        txn_id = int(body["txn_id"])
        from_key = int(body["from_key"])
        to_key = int(body["to_key"])
        amount = int(body["amount"])
        parts = ["accounts", from_key, to_key, amount]
        problem, status = check_user(txn_id, "transfer", parts, "accounts")
        if problem is not None:
            return error_reply(problem, status)
        do_transfer(txn_id, from_key, to_key, amount)
        return jsonify({"ok": True})
    except bad_input:
        return error_reply("bad request", 400)
    except Exception as e:
        return error_reply(str(e), 400)


def commit_route():
    try:
        transaction_manager.commit(int(get_body()["txn_id"]))
        return jsonify({"ok": True})
    except bad_input:
        return error_reply("bad request", 400)
    except Exception as e:
        return error_reply(str(e), 400)


def abort_route():
    try:
        transaction_manager.abort(int(get_body()["txn_id"]))
        return jsonify({"ok": True})
    except bad_input:
        return error_reply("bad request", 400)
    except Exception as e:
        return error_reply(str(e), 400)


app.add_url_rule("/", "home", home, methods=["GET"])
app.add_url_rule("/api/locks", "locks", locks_route, methods=["GET"])
app.add_url_rule("/api/graph", "graph", graph_route, methods=["GET"])
app.add_url_rule("/api/deadlocks", "deadlocks", deadlocks_route, methods=["GET"])
app.add_url_rule("/api/alerts", "alerts", alerts_route, methods=["GET"])
app.add_url_rule("/api/demo/without_locks", "demo_without", demo_without_route, methods=["POST"])
app.add_url_rule("/api/demo/with_locks", "demo_with", demo_with_route, methods=["POST"])
app.add_url_rule("/api/login", "login", login_route, methods=["POST"])
app.add_url_rule("/api/begin", "begin", begin_route, methods=["POST"])
app.add_url_rule("/api/read", "read", read_route, methods=["POST"])
app.add_url_rule("/api/write", "write", write_route, methods=["POST"])
app.add_url_rule("/api/transfer", "transfer", transfer_route, methods=["POST"])
app.add_url_rule("/api/commit", "commit", commit_route, methods=["POST"])
app.add_url_rule("/api/abort", "abort", abort_route, methods=["POST"])


def start_api():
    deadlock_detector.start()
    print("api running on", config.API_HOST, config.API_PORT)
    app.run(host=config.API_HOST, port=config.API_PORT, threaded=True, debug=False, use_reloader=False)


if __name__ == "__main__":
    start_api()
