from ankit import api
from tanu import attack_correlator

client = api.app.test_client()


def test_home():
    res = client.get("/")
    assert res.status_code == 200
    assert "html" in res.get_data(as_text=True)
    print("PASS test_home")


def test_locks():
    res = client.get("/api/locks")
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)
    print("PASS test_locks")


def test_graph():
    res = client.get("/api/graph")
    assert res.status_code == 200
    assert isinstance(res.get_json(), dict)
    print("PASS test_graph")


def test_deadlocks_and_alerts():
    res = client.get("/api/deadlocks")
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)
    res = client.get("/api/alerts")
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)
    print("PASS test_deadlocks_and_alerts")


def test_begin_empty_body():
    res = client.post("/api/begin")
    assert res.status_code == 400
    assert res.get_json() == {"error": "bad request"}
    print("PASS test_begin_empty_body")


def test_begin_quarantined():
    attack_correlator.quarantined.append("mallory")
    res = client.post("/api/begin", json={"user": "mallory"})
    assert res.status_code == 403
    assert res.get_json() == {"error": "quarantined"}
    print("PASS test_begin_quarantined")


def test_commit_unknown():
    res = client.post("/api/commit", json={"txn_id": 987654})
    assert res.status_code == 400
    print("PASS test_commit_unknown")


def run_all():
    attack_correlator.reset_all()
    test_home()
    test_locks()
    test_graph()
    test_deadlocks_and_alerts()
    test_begin_empty_body()
    test_begin_quarantined()
    test_commit_unknown()
    attack_correlator.reset_all()
    print("all api tests passed")


if __name__ == "__main__":
    run_all()
