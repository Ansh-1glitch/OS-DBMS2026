import threading
import time

from ankit import transaction_manager
from ankit import victim_selector
from ansh import deadlock_event_log
from shared import config
from tanishka import lock_manager
from tanu import attack_correlator

running = False
thread = None


def add_edge(graph, waiter, holder):
    if waiter == holder:
        return
    if waiter not in graph:
        graph[waiter] = []
    if holder not in graph[waiter]:
        graph[waiter].append(holder)


def get_wait_graph():
    graph = {}
    for lock in lock_manager.get_locks():
        ahead = []
        for waiter in lock["waiting"]:
            for holder in lock["holders"]:
                add_edge(graph, waiter, holder)
            for other in ahead:
                add_edge(graph, waiter, other)
            ahead.append(waiter)
    return graph


def visit(graph, node, visited, path):
    visited.append(node)
    path.append(node)
    for nxt in graph.get(node, []):
        if nxt in path:
            return path[path.index(nxt):]
        if nxt not in visited:
            cycle = visit(graph, nxt, visited, path)
            if len(cycle) > 0:
                return cycle
    path.pop()
    return []


def find_cycle(graph):
    visited = []
    for node in graph:
        if node not in visited:
            cycle = visit(graph, node, visited, [])
            if len(cycle) > 0:
                return cycle
    return []


def get_users(cycle):
    users = []
    for txn_id in cycle:
        user = transaction_manager.get_user(txn_id)
        if user is not None:
            users.append(user)
    return users


def detect_once():
    cycle = find_cycle(get_wait_graph())
    if len(cycle) == 0:
        return False
    victim = victim_selector.select_victim(cycle)
    if victim is None:
        print("deadlock found but no active victim", cycle)
        return False
    users = get_users(cycle)
    deadlock_event_log.add_event(cycle, victim, users)
    attack_correlator.record_deadlock(users, time.time())
    transaction_manager.abort(victim)
    print("deadlock cycle", cycle, "victim", victim)
    return True


def run_loop():
    while running:
        try:
            detect_once()
        except Exception as e:
            print("detector error:", e)
        time.sleep(config.DEADLOCK_CHECK_SECONDS)


def start():
    global running, thread
    if running:
        return
    running = True
    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()


def stop():
    global running
    running = False
    if thread is not None:
        thread.join(timeout=2)


def start_detector():
    start()


def stop_detector():
    stop()
