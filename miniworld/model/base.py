from collections import defaultdict


class Base:
    counter = defaultdict(lambda: 0)

    @staticmethod
    def id_provider(cls):
        """ All decorated subclasses as well as objects subclassing the id_provider
         have a shared counter for instance creation"""
        cls.id_provider = cls
        return cls

    def __new__(cls, *args, **kwargs):
        count = Base.counter[cls.id_provider]
        Base.counter[cls.id_provider] += 1
        instance = super().__new__(cls)
        setattr(instance, '_id', count)
        return instance
