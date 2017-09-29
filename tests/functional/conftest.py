def assert_topologies_equal(t1, t2):
    """ Compare topologies but ignore order inside value list """
    assert t1.keys() == t2.keys()

    t1s, t2s = {}, {}
    for key in t1.keys():
        # convert values to sets to compare so that order does not matter
        t1s[key] = set(t1[key])
        t2s[key] = set(t2[key])

    assert t1s == t2s
