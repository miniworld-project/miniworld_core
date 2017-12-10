from miniworld.model.base import Base


class TestBase:

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
