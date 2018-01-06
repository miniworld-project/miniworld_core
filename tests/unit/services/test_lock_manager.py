import pytest

from miniworld.model.Lock import Resource, Type, LockEntry
from miniworld.service.LockManager import LockManager


class TestLockManager:
    @pytest.mark.parametrize('type', iter(Type))
    def test_acquire_no_locks(self, type: Type):
        lm = LockManager()
        lm._locks = {}
        lock_entry = lm.acquire(Resource.emulation, type)
        assert isinstance(lock_entry, LockEntry)
        assert lock_entry.type == type

    @pytest.mark.parametrize('type', iter(Type))
    def test_acquire_fail_write(self, type: Type):
        lm = LockManager()
        lm._locks = {Resource.emulation: [LockEntry(Type.write)]}
        with pytest.raises(lm.Locked):
            lm.acquire(Resource.emulation, type)

    def test_acquire_read(self):
        lm = LockManager()
        lm._locks = {Resource.emulation: [LockEntry(Type.read)]}
        lock_entry = lm.acquire(Resource.emulation, Type.read)
        assert isinstance(lock_entry, LockEntry)

    def test_lock(self):
        lm = LockManager()

        # exception should not be catched by context manager
        with pytest.raises(RuntimeError):
            with lm.lock(Resource.emulation, Type.write):
                raise RuntimeError('ups')
        for resource, locks in lm._locks.items():
            assert len(locks) == 0
