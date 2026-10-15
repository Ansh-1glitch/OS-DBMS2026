import sys
import threading
import time
import urllib.request
import webbrowser

from ankit import api
from ansh import deadlock_detector
from ansh import deadlock_event_log
from shared import config
from tanishka import db_wrapper
from tanu import attack_correlator
from tanu import client_sim
from tanu import rate_limiter


def base_url():
    return "http://" + config.API_HOST + ":" + str(config.API_PORT)


def reset_state():
    attack_correlator.reset_all()
    rate_limiter.reset_rates()
    deadlock_event_log.reset_events()
    db_wrapper.reset_accounts()


def start_server():
    server = threading.Thread(target=api.start_api, daemon=True)
    server.start()


def wait_for_server():
    url = base_url() + "/api/locks"
    for tries in range(30):
        try:
            with urllib.request.urlopen(url, timeout=2) as res:
                res.read()
            return True
        except Exception:
            time.sleep(0.5)
    return False


def has_alert(alerts, user):
    for alert in alerts:
        if alert["user"] == user:
            return True
    return False


def begin_status(user):
    status, reply = client_sim.post("/api/begin", {"user": user})
    if status == 200:
        client_sim.post("/api/abort", {"txn_id": reply["txn_id"]})
    return status


def check_result():
    alerts = attack_correlator.get_alerts()
    return {
        "mallory_status": begin_status("mallory"),
        "alice_status": begin_status("alice"),
        "mallory_alert": has_alert(alerts, "mallory"),
        "alice_alert": has_alert(alerts, "alice"),
        "events": len(deadlock_event_log.get_events()),
    }


def find_failures(result):
    failed = []
    if result["mallory_status"] != 403:
        failed.append("mallory_status should be 403")
    if result["alice_status"] != 200:
        failed.append("alice_status should be 200")
    if result["mallory_alert"] is not True:
        failed.append("mallory_alert should be True")
    if result["alice_alert"] is not False:
        failed.append("alice_alert should be False")
    if result["events"] < 1:
        failed.append("events should be at least 1")
    return failed


def print_summary(result):
    print("")
    print("summary:")
    for key in result:
        print("  " + key + ":", result[key])
    failed = find_failures(result)
    if len(failed) == 0:
        print("DEMO PASS")
        return 0
    print("DEMO FAIL")
    for text in failed:
        print("  failed check:", text)
    return 1


def open_browser(url):
    try:
        webbrowser.open(url)
    except Exception as e:
        print("could not open browser:", e)


def keep_running():
    print("Dashboard is running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    deadlock_detector.stop()
    print("stopped")


def run_demo(once):
    reset_state()
    start_server()
    if not wait_for_server():
        print("server did not start (is port " + str(config.API_PORT) + " already in use?)")
        return 1
    url = base_url() + "/"
    print("dashboard:", url)
    if not once:
        open_browser(url)
        time.sleep(3)
    result = client_sim.run_simulation(4)
    if result is not None:
        print("simulation returned:", result)
    code = print_summary(check_result())
    if not once:
        keep_running()
    return code


def main():
    once = "once" in sys.argv[1:]
    sys.exit(run_demo(once))


if __name__ == "__main__":
    main()
