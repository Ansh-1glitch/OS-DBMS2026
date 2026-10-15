from shared import config
from tanu import attack_correlator


def test_below_limit():
    attack_correlator.reset_all()
    t = 100
    for i in range(config.ATTACK_LIMIT - 1):
        attack_correlator.record_deadlock(["bob"], t + i)
    assert not attack_correlator.is_quarantined("bob")
    assert attack_correlator.get_alerts() == []
    print("PASS test_below_limit")


def test_reach_limit():
    attack_correlator.reset_all()
    t = 100
    for i in range(config.ATTACK_LIMIT):
        attack_correlator.record_deadlock(["mallory"], t + i)
    assert attack_correlator.is_quarantined("mallory")
    alerts = attack_correlator.get_alerts()
    assert len(alerts) == 1
    assert alerts[0]["user"] == "mallory"
    print("PASS test_reach_limit")


def test_old_events_ignored():
    attack_correlator.reset_all()
    attack_correlator.record_deadlock(["bob"], 0)
    attack_correlator.record_deadlock(["bob"], 1)
    attack_correlator.record_deadlock(["bob"], 500)
    assert len(attack_correlator.user_times["bob"]) == 1
    assert not attack_correlator.is_quarantined("bob")
    print("PASS test_old_events_ignored")


def test_release_user():
    attack_correlator.reset_all()
    for i in range(config.ATTACK_LIMIT):
        attack_correlator.record_deadlock(["mallory"], 100 + i)
    assert attack_correlator.is_quarantined("mallory")
    attack_correlator.release_user("mallory")
    assert not attack_correlator.is_quarantined("mallory")
    assert "mallory" not in attack_correlator.user_times
    print("PASS test_release_user")


def test_attacker_not_normal():
    attack_correlator.reset_all()
    attack_correlator.record_deadlock(["attacker", "normal"], 100)
    for i in range(1, config.ATTACK_LIMIT + 2):
        attack_correlator.record_deadlock(["attacker", "other" + str(i)], 100 + i)
        assert not attack_correlator.is_quarantined("normal")
    assert attack_correlator.is_quarantined("attacker")
    assert len(attack_correlator.get_alerts()) == 1
    print("PASS test_attacker_not_normal")


def run_all():
    test_below_limit()
    test_reach_limit()
    test_old_events_ignored()
    test_release_user()
    test_attacker_not_normal()
    attack_correlator.reset_all()
    print("all attack correlator tests passed")


if __name__ == "__main__":
    run_all()
