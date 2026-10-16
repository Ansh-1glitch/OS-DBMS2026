import os
import subprocess
import sys

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
folders = ["tanishka", "ansh", "ankit", "tanu"]
needs_mysql = [
    "test_db_wrapper",
    "test_wal",
    "test_transaction_manager",
    "test_security_gateway",
    "test_deadlock_live",
    "test_lost_update_demo",
    "test_api_live",
]


def find_modules(skip_mysql):
    modules = []
    for folder in folders:
        names = sorted(os.listdir(os.path.join(root, folder, "tests")))
        for file_name in names:
            if not file_name.startswith("test_") or not file_name.endswith(".py"):
                continue
            name = file_name[:-3]
            if skip_mysql and name in needs_mysql:
                continue
            modules.append(folder + ".tests." + name)
    return modules


def run_module(module):
    result = subprocess.run([sys.executable, "-m", module], cwd=root, capture_output=True, text=True)
    if result.returncode == 0:
        print("PASS", module)
        return True
    print("FAIL", module)
    print(result.stdout)
    print(result.stderr)
    return False


def main():
    skip_mysql = "nomysql" in sys.argv[1:]
    passed = 0
    failed = 0
    for module in find_modules(skip_mysql):
        if run_module(module):
            passed = passed + 1
        else:
            failed = failed + 1
    print("passed:", passed, "failed:", failed)
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
