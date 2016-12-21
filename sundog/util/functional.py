def const(value, *_, **__):
    return lambda *_, **__: value


def catching(computation, catcher, exception=Exception):
    try:
        return computation()
    except exception as e:
        return catcher(e)


def defaulting(computation, value, exception=Exception):
    return catching(
        computation=computation,
        catcher=const(value),
        exception=exception,
    )


def mutate(x, f):
    f(x)
    return x


def modify_dict(dictionary, key, default, function):
    if key not in dictionary:
        dictionary[key] = default
    dictionary[key] = function(dictionary[key])
    return dictionary
