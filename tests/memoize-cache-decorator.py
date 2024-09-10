from decorator import decorator
@decorator
def memoize(func, *args, **kw):
    # Author: Michele Simoniato
    # Source: http://pypi.python.org/pypi/decorator
    if not hasattr(func, 'cache'):
        func.cache = {}
    if kw: # frozenset is used to ensure hashability
        key = args, frozenset(kw.iteritems())
    else:
        key = args
    cache = func.cache # attribute added by memoize
    if key in cache:
        return cache[key]
    else:
        cache[key] = result = func(*args, **kw)
        return result
