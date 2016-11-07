from django.conf.urls import url
from django.db.models import Model
from django.utils.decorators import method_decorator
from django.views import View
from importlib import import_module
from pkgutil import iter_modules
from sys import modules


class Route:
    '''
    Route pattern assigned to a view.
    '''
    def __init__(self, regex, name):
        self.regex = regex
        self.name = name


def route(regex, name=None):
    '''
    Decorator to add route configuration to views.

    Omitting the name will derive the view name from the view object
    ``__name__``.  The name may be a string or an iterable yielding strings.

    Sample usage:

    # views.py
    from django.http import HttpResponse
    from django.views import View
    from django_routing import route

    @route(r'^some/route/?$')
    def some_route(request):
        return HttpResponse('Hello, world!')

    @route(r'^another/route/?$', name='second_hello')
    class AnotherRoute(View):
        def get(self, request):
            return HttpResponse("What's up, world?")

    # urls.py
    import views
    from django_routing import package_urls
    urlpatterns = package_urls(views)
    '''

    def modify(dictionary, key, default, function):
        if key not in dictionary:
            dictionary[key] = default
        dictionary[key] = function(dictionary[key])
        return dictionary

    def routed(view):
        nonlocal regex
        nonlocal name
        modify(
            modules[view.__module__].__dict__,
            Route,
            {},
            lambda module_routes:
                modify(
                    module_routes,
                    view,
                    [],
                    lambda view_routes:
                        view_routes + [
                            Route(regex, name_)
                            for name_ in (
                                [name]
                                if isinstance(name, str)
                                else name
                            )
                        ]
                )
        )
        return view
    return routed


decorate_view = (
    lambda decorator:
        lambda view: (
            method_decorator(decorator, name='dispatch')(view)
            if isinstance(view, type) and issubclass(view, View)
            else decorator(view)
        )
)


def filter_package_modules(package, filter):
    return [
        x
        for module in walk_packages(package)
        for x in filter(module)
    ]


def module_urls(module):
    return [
        url(
            regex=route.regex,
            name=(
                route.name
                if route.name
                else view.__module__ + '.' + view.__name__
            ),
            view=(
                view.as_view()
                if isinstance(view, type) and issubclass(view, View)
                else view
            ),
        )
        for view, routes in module.__dict__.get(Route, {}).items()
        for route in routes
    ]


def package_urls(package):
    return filter_package_modules(package, module_urls)


def package_models(package):
    return filter_package_modules(
        package,
        lambda module: [
            value
            for name, value in module.__dict__.items()
            if isinstance(value, type) and issubclass(value, Model)
        ]
    )


# The Python standard library implementation of walk_packages is wrong; see
#
#     https://hg.python.org/cpython/file/3.5/Lib/pkgutil.py
#
# The version included here is fixed although less general.

def walk_packages(root):
    for importer, name, ispkg in iter_modules(root.__path__):
        try:
            module = import_module(root.__name__ + '.' + name)
            yield module

            if ispkg:
                yield from walk_packages(module)
        except ImportError:
            continue
