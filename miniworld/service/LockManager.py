import contextlib
import threading

from miniworld.model.Lock import Type, Resource, LockEntry
from miniworld.singletons import singletons


class LockManager:
    class Locked(Exception):
        pass

    def __init__(self):
        self._locks = {}  # type: Dict[Lock.Resource, List[LockEntry]]
        self._plock = threading.Lock()
        self._logger_factory = singletons.logger_factory.get_logger(self)

    def acquire(self, resource: Resource, type: Type) -> LockEntry:
        """
        Raises
        ------
        Locked
        """
        self._logger_factory.info('acquire {} lock on {}'.format(type, resource))

        def add_lock_entry() -> LockEntry:
            lock_entry = LockEntry(type)
            current_locks.append(lock_entry)
            return lock_entry

        with self._plock:

            # init locks for resource
            if resource not in self._locks:
                self._locks[resource] = []

            current_locks = self._locks[resource]  # type: List[LockEntry]
            # only one write lock at a time
            if any(lock_entry.type == Type.write for lock_entry in current_locks):
                raise self.Locked()

            # no write lock exists
            return add_lock_entry()

            if type == Type.write and len(current_locks) > 0:
                # there is at least one read lock
                raise self.Locked(repr(self.locks))

            raise self.Locked()

    def release(self, lock_entry: LockEntry) -> bool:
        with self._plock:
            for resource in Resource:
                current_locks = self._locks[resource]  # type: List[LockEntry]
                idx = None
                for idx, a_lock_entry in enumerate(current_locks):
                    if a_lock_entry == lock_entry:
                        break
                if idx is not None:
                    del current_locks[idx]
                    self._logger_factory.info('released lock {}'.format(lock_entry))
                    return

    @contextlib.contextmanager
    def lock(self, resource: Resource, type: Type) -> bool:
        lock_entry = self.acquire(resource=resource, type=type)
        try:
            yield
        except Exception:
            raise
        finally:
            self.release(lock_entry)
