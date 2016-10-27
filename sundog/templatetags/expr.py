# app/common/templatetags/expr.py

from django import template
from django.utils.translation import gettext_lazy as _
import re


register = template.Library()


class ExprNode(template.Node):
    """
    This tag can be used to calculate an arbitrary python expression,
    because Django is obnoxious about having you not calculate things.
    To save result in another template variable:
    {% expr "1" as var1 %}
    {% expr [0, 1, 2] as var2 %}
    {% expr _('Menu') as var3 %}
    {% expr var1 + "abc" as var4 %}
    ...
    {{ var1 }}
    To directly output result:
    {% expr 3 %}
    {% expr "".join(["a", "b", "c"]) %}
    Syntax:
    {% expr python_expression as variable_name %}
    {% expr python_expression %}
    python_expression can be any valid python expression,
    and you can even use _() to translate a string. Expr tag
    also has access to context variables.
    See http://djangosnippets.org/snippets/9/, but some changes
    were made since the structure of the context object has changed.
    """

    def __init__(self, expr_string, var_name):
        self.expr_string = expr_string
        self.var_name = var_name

    def render(self, context):
        try:
            clist = list(context)
            clist.reverse()
            d = {}
            d['_'] = _
            for c in clist:
                for item in c:
                    d[item] = c[item]
                    # TODO: is the item ever a dict? this may have been
                    # a change from 0.96 to 1.0
                    if isinstance(item, dict):
                        d.update(item)
            if self.var_name:
                context[self.var_name] = eval(self.expr_string, d)
                return ''
            else:
                return str(eval(self.expr_string, d))
        except Exception as e:
            return str(e)


r_expr = re.compile(r'(.*?)\s+as\s+(\w+)', re.DOTALL)


def do_expr(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires arguments" % token.contents[0]
        )
    m = r_expr.search(arg)
    if m:
        expr_string, var_name = m.groups()
    else:
        if not arg:
            raise template.TemplateSyntaxError(
                "%r tag at least require one argument" % tag_name
            )

        expr_string, var_name = arg, None
    return ExprNode(expr_string, var_name)


do_expr = register.tag('expr', do_expr)
