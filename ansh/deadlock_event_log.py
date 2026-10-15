import threading
import time

events = []
event_lock = threading.Lock()


def add_event(cycle, victim, users):
    event = {"cycle": list(cycle), "victim": victim, "users": list(users), "time": time.time()}
    with event_lock:
        events.append(event)


def save_event(cycle, victim, users):
    add_event(cycle, victim, users)


def get_events():
    result = []
    with event_lock:
        for event in events:
            copy = dict(event)
            copy["cycle"] = list(event["cycle"])
            copy["users"] = list(event["users"])
            result.append(copy)
    return result


def reset_events():
    with event_lock:
        del events[:]
