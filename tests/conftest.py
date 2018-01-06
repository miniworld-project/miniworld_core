import pytest


@pytest.fixture(scope='session')
def core_topologies_dir():
    return 'tests/core_topologies/'
