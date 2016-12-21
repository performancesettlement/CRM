from datatableview.columns import CompoundColumn, DisplayColumn, TextColumn
from datatableview.views import XEditableDatatableView
from django.template.loader import render_to_string
from sundog.util.functional import const


def format_column(label, template, fields):
    return CompoundColumn(
        label,
        sources=[
            TextColumn(source=field)
            for field in fields
        ],
        processor=(
            lambda *args, **kwargs: template.format(
                **{
                    field: values.get(field, '')
                    for values in [
                        dict(
                            zip(
                                fields,
                                kwargs.get('default_value', []),
                            ),
                        ),
                    ]
                    for field in fields
                },
            )
        ),
    )


def template_column(
    label,
    template_name,
    context={},
    context_builder=const({}),
):
    return DisplayColumn(
        label=label,
        processor=(
            lambda instance, *args, **kwargs:
                render_to_string(
                    template_name=template_name,
                    context={
                        'instance': instance,
                        'args': args,
                        'kwargs': kwargs,
                        **context,
                        **context_builder(
                            instance=instance,
                            context=context,
                            label=label,
                            template_name=template_name,
                            *args,
                            **kwargs,
                        ),
                    },
                )
        ),
    )


class SundogDatatableView(XEditableDatatableView):
    # Override this attribute with the list of column names (not labels, just
    # the internal names used in code) for which a per-column search input
    # should be provided.
    searchable_columns = []

    # This enables the table footer, which is actually displayed just below the
    # table header and includes all of the per-column search input fields.
    footer = True

    def get_datatable(self):
        datatable = super().get_datatable()

        # Add the data-config-searchable="true" attribute to column headers for
        # columns listed in self.searchable_columns.  This makes those columns
        # get a text input box for column-specific filtering.
        for name, column in datatable.columns.items():
            if name in self.searchable_columns:
                # The attributes field of Column objects is implemented with
                # the @property decorator, so the only way to override it on a
                # per-instance basis is to change the class of the Column object
                # dynamically.  See http://stackoverflow.com/a/31591589/1392731
                attributes_ = column.attributes

                class SearchColumn(type(column)):
                    attributes = attributes_ + ' data-config-searchable="true"'

                    # Subclassing the original column class without resetting
                    # these two class fields to empty values would make the
                    # metaclass for columns override registrations for the types
                    # handled by the original class with this modified subclass.
                    # This would introduce the attribute for searchable columns
                    # anywhere those types are used for columns.  To avoid this,
                    # set these fields to the original values in the Column
                    # class which specify no registrations by the metaclass.
                    # Details in datatableview.columns.ColumnMetaclass.__new__
                    model_field_class = None
                    handles_field_classes = []

                column.__class__ = SearchColumn

        return datatable
