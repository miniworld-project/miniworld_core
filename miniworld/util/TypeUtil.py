
def type_check(obj, _type):
    if not isinstance(obj, _type):
        raise ValueError("The value of '%s' has to be a subclass of '%s'. Actual type:'%s" % (obj, _type, _type.__class__))
