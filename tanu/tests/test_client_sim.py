import threading
import time

from flask import Flask, jsonify

from tanu import client_sim

app = Flask(__name__)
base = "http://127.0.0.1:5099"


def ok_route():
    return jsonify({"ok": True})


def bad_route():
    return jsonify({"error": "x"}), 400


def text_route():
    return "not json", 200, {"Content-Type": "text/plain"}


app.add_url_rule("/ok", "ok", ok_route, methods=["POST"])
app.add_url_rule("/bad", "bad", bad_route, methods=["POST"])
app.add_url_rule("/text", "text", text_route, methods=["POST"])


def run_server():
    app.run(host="127.0.0.1", port=5099, threaded=True, debug=False, use_reloader=False)


def start_server():
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    for i in range(20):
        status, reply = client_sim.post_url(base + "/ok", {})
        if status == 200:
            return True
        time.sleep(0.2)
    return False


def test_ok():
    assert client_sim.post_url(base + "/ok", {"a": 1}) == (200, {"ok": True})
    print("PASS test_ok")


def test_bad():
    assert client_sim.post_url(base + "/bad", {}) == (400, {"error": "x"})
    print("PASS test_bad")


def test_text():
    status, reply = client_sim.post_url(base + "/text", {})
    assert status == 0
    assert "error" in reply
    print("PASS test_text")


def test_unreachable():
    status, reply = client_sim.post_url("http://127.0.0.1:1/x", {})
    assert status == 0
    assert "error" in reply
    print("PASS test_unreachable")


def run_all():
    assert start_server()
    test_ok()
    test_bad()
    test_text()
    test_unreachable()
    print("all client sim tests passed")


if __name__ == "__main__":
    run_all()
