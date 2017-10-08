import pytest

import miniworld


@pytest.fixture(autouse=True)
def fresh_env():
    miniworld.init()
