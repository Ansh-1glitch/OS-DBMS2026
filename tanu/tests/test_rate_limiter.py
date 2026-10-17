from shared import config
from tanu import rate_limiter


def test_limit():
    rate_limiter.reset_rates()
    for i in range(config.RATE_LIMIT_PER_MINUTE):
        assert rate_limiter.check_rate("alice")
    assert not rate_limiter.check_rate("alice")
    print("PASS test_limit")


def test_other_user():
    rate_limiter.reset_rates()
    for i in range(config.RATE_LIMIT_PER_MINUTE + 5):
        rate_limiter.check_rate("alice")
    assert rate_limiter.check_rate("bob")
    print("PASS test_other_user")


def run_all():
    test_limit()
    test_other_user()
    rate_limiter.reset_rates()
    print("all rate limiter tests passed")


if __name__ == "__main__":
    run_all()
