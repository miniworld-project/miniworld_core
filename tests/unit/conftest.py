import pytest
from graphene.test import Client

import miniworld
from miniworld.api.webserver import schema


@pytest.fixture(autouse=True)
def fresh_env():
    miniworld.init()


@pytest.fixture
def client():
    client = Client(schema)
    return client
