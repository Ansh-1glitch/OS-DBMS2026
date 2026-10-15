from ansh import wait_for_graph


def clear():
    wait_for_graph.graph.clear()


def test_add_edges():
    clear()
    wait_for_graph.add_edge(1, 2)
    wait_for_graph.add_edge(1, 3)
    wait_for_graph.add_edge(2, 3)
    assert wait_for_graph.get_graph() == {1: [2, 3], 2: [3]}
    print("PASS test_add_edges")


def test_ignore_duplicate_and_self():
    clear()
    wait_for_graph.add_edge(1, 2)
    wait_for_graph.add_edge(1, 2)
    wait_for_graph.add_edge(3, 3)
    assert wait_for_graph.get_graph() == {1: [2]}
    print("PASS test_ignore_duplicate_and_self")


def test_remove_edges():
    clear()
    wait_for_graph.add_edge(1, 2)
    wait_for_graph.add_edge(2, 1)
    wait_for_graph.remove_edges(1)
    assert wait_for_graph.get_graph() == {2: [1]}
    print("PASS test_remove_edges")


def test_remove_node():
    clear()
    wait_for_graph.add_edge(1, 2)
    wait_for_graph.add_edge(3, 2)
    wait_for_graph.add_edge(3, 4)
    wait_for_graph.add_edge(2, 4)
    wait_for_graph.remove_node(2)
    assert wait_for_graph.get_graph() == {3: [4]}
    print("PASS test_remove_node")


def test_copy():
    clear()
    wait_for_graph.add_edge(1, 2)
    copy = wait_for_graph.get_graph()
    copy[1].append(5)
    copy[7] = [8]
    assert wait_for_graph.get_graph() == {1: [2]}
    print("PASS test_copy")


def run_all():
    test_add_edges()
    test_ignore_duplicate_and_self()
    test_remove_edges()
    test_remove_node()
    test_copy()
    clear()
    print("all wait graph tests passed")


if __name__ == "__main__":
    run_all()
