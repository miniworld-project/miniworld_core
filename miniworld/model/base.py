class Base:
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
