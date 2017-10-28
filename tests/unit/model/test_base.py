from miniworld.model.base import Base


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
