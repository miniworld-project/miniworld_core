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

    def __init__(self, *args, **kwargs):
        """ Generic init method for all domain models """
        if args:
            raise ValueError('domain models only support keyword arguments')

        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        if getattr(self, '__slots__', None) is not None:
            raise RuntimeError('__repr__ assumes there are not slots defined')

        attributes = self.__dict__
        attributes = ['{key}={value!r}'.format(key=key, value=value) for key, value in attributes.items()]

        return '{class_name}({attributes})'.format(
            class_name=self.__class__.__name__,
            attributes=', '.join(attributes)
        )
