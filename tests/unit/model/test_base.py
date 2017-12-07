from miniworld.model.base import Base
from miniworld.singletons import singletons


class TestBase:
    def test_id_provider(self):
        @Base.id_provider
        class X(Base):
            pass

        class Y(X):
            pass

        @Base.id_provider
        class Z(Base):
            pass

        x1 = X()
        x2 = X()
        y = Y()
        x3 = X()

        assert x1._id == 0
        assert x2._id == 1
        assert y._id == 2
        assert x3._id == 3

        # new id provider
        assert Z()._id == 0

    def test_reset_class(self):
        """ Check that id generation is correctly resetted """

        @Base.id_provider
        class Foo(Base):
            pass

        foo1 = Foo()
        assert foo1._id == 0
        singletons.simulation_state_gc.reset_simulation_scenario_state()
        foo2 = Foo()
        assert foo2._id == 0

    def test_init(self):
        class Sub(Base):
            pass

        sub = Sub(foo='foo', bar='bar')
        assert sub.foo == 'foo'
        assert sub.bar == 'bar'

    def test_repr(self):
        class Sub(Base):
            pass

        sub = Sub(foo='foo', bar='bar')
        assert repr(sub) == "Sub(foo='foo', bar='bar')"
