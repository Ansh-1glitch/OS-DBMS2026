import threading

from shared import config
from tanishka import db_wrapper

user_times = {}
quarantined = []
alert_list = []
alert_lock = threading.Lock()


def unique(users):
    result = []
    for user in users:
        if user not in result:
            result.append(user)
    return result


def add_time(user, time):
    if user not in user_times:
        user_times[user] = []
    user_times[user].append(time)
    kept = []
    for t in user_times[user]:
        if t >= time - config.ATTACK_WINDOW_SECONDS:
            kept.append(t)
    user_times[user] = kept


def highest_count():
    best = 0
    for user in user_times:
        if len(user_times[user]) > best:
            best = len(user_times[user])
    return best


def save_alert(user, reason):
    try:
        db_wrapper.insert("alerts", {"username": user, "reason": reason})
    except Exception:
        print("could not save alert")


def record_deadlock(users, time):
    new_alerts = []
    with alert_lock:
        users = unique(users)
        for user in users:
            add_time(user, time)
        best = highest_count()
        for user in users:
            count = len(user_times[user])
            if user not in quarantined and count >= config.ATTACK_LIMIT and count == best:
                quarantined.append(user)
                reason = "deadlock count " + str(count) + " in window"
                alert_list.append({"user": user, "reason": reason, "time": time})
                new_alerts.append((user, reason))
                print("quarantined user", user, "-", reason)
    for item in new_alerts:
        save_alert(item[0], item[1])


def is_quarantined(user):
    with alert_lock:
        return user in quarantined


def release_user(user):
    with alert_lock:
        if user in quarantined:
            quarantined.remove(user)
        if user in user_times:
            del user_times[user]


def get_alerts():
    result = []
    with alert_lock:
        for alert in alert_list:
            result.append(dict(alert))
    return result


def reset_all():
    with alert_lock:
        user_times.clear()
        del quarantined[:]
        del alert_list[:]
