from collections import defaultdict
from miniworld.singletons import singletons


class Base:
    counter = defaultdict(lambda: 0)

    @staticmethod
    def id_provider(cls):
        """ All decorated subclasses as well as objects subclassing the id_provider
         have a shared counter for instance creation"""
        cls.id_provider = cls
        return cls

    @classmethod
    def reset_class(cls):
        cls.counter = defaultdict(lambda: 0)

    def __new__(cls, *args, **kwargs):
        singletons.simulation_state_gc.add_static(Base)
        count = Base.counter[cls.id_provider]
        Base.counter[cls.id_provider] += 1
        instance = super().__new__(cls)
        setattr(instance, '_id', count)
        return instance
