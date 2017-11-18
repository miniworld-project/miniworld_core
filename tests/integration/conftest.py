import pytest

import miniworld
from tests.unit.conftest import fresh_env  # noqa


@pytest.fixture(autouse=True)  # noqa
def db_fresh_env(fresh_env):
    miniworld.init_db()
