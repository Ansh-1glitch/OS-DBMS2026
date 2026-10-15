from ansh import deadlock_detector
from ansh import deadlock_event_log


def test_no_cycle():
    graph = {1: [2], 2: [3], 4: [3]}
    assert deadlock_detector.find_cycle(graph) == []
    assert deadlock_detector.find_cycle({}) == []
    print("PASS test_no_cycle")


def test_two_node_cycle():
    cycle = deadlock_detector.find_cycle({1: [2], 2: [1]})
    assert sorted(cycle) == [1, 2]
    print("PASS test_two_node_cycle")


def test_three_node_cycle_with_tail():
    graph = {9: [8], 8: [1], 1: [2], 2: [3], 3: [1]}
    cycle = deadlock_detector.find_cycle(graph)
    assert sorted(cycle) == [1, 2, 3]
    print("PASS test_three_node_cycle_with_tail")


def test_self_wait():
    assert deadlock_detector.find_cycle({5: [5]}) == [5]
    print("PASS test_self_wait")


def test_event_log():
    deadlock_event_log.reset_events()
    deadlock_event_log.add_event([1, 2], 2, ["u1", "u2"])
    result = deadlock_event_log.get_events()
    assert len(result) == 1
    assert result[0]["cycle"] == [1, 2]
    assert result[0]["victim"] == 2
    result[0]["cycle"].append(99)
    result.append({})
    again = deadlock_event_log.get_events()
    assert len(again) == 1
    assert again[0]["cycle"] == [1, 2]
    deadlock_event_log.reset_events()
    assert deadlock_event_log.get_events() == []
    print("PASS test_event_log")


def run_all():
    test_no_cycle()
    test_two_node_cycle()
    test_three_node_cycle_with_tail()
    test_self_wait()
    test_event_log()
    print("all deadlock detector tests passed")


if __name__ == "__main__":
    run_all()
