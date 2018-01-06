import pytest

from miniworld.service.persistence.interfaces import InterfacePersistenceService


class TestInterfacePersistenceService:
    @pytest.fixture
    def service(self):
        return InterfacePersistenceService()

    def test_get(self, service, connections):
        interface = service.get(interface_id=0)
        assert interface._id == 0
