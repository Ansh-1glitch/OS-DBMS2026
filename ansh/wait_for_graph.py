import threading

graph = {}
graph_lock = threading.Lock()


def add_edge(waiter, holder):
    if waiter == holder:
        return
    with graph_lock:
        if waiter not in graph:
            graph[waiter] = []
        if holder not in graph[waiter]:
            graph[waiter].append(holder)


def remove_edges(txn_id):
    with graph_lock:
        if txn_id in graph:
            del graph[txn_id]


def remove_node(txn_id):
    with graph_lock:
        if txn_id in graph:
            del graph[txn_id]
        for waiter in list(graph.keys()):
            if txn_id in graph[waiter]:
                graph[waiter].remove(txn_id)
            if len(graph[waiter]) == 0:
                del graph[waiter]


def get_graph():
    copy = {}
    with graph_lock:
        for waiter in graph:
            holders = []
            for holder in graph[waiter]:
                holders.append(holder)
            copy[waiter] = holders
    return copy
