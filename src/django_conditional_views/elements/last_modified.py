import datetime
import os
from typing import Optional

from django.core.exceptions import ImproperlyConfigured
from django.template.loader import select_template
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin

from .base import BaseLastModifiedElement

__all__ = ['TemplateLastModified', 'ObjectLastModified', 'QuerySetLastModified']


class TemplateLastModified(BaseLastModifiedElement):
    """Returns the last modified time of the template file.

    Note that on ListView's self.object_list = self.get_queryset() must have already been run,
    see the ConditionalGetListViewMixin for an example implementation.
    """
    view_class = TemplateResponseMixin

    def value(self, view: TemplateResponseMixin) -> Optional[datetime.datetime]:
        t = select_template(view.get_template_names())
        local_tz = datetime.datetime.now().astimezone().tzinfo
        return datetime.datetime.fromtimestamp(os.stat(t.origin.name).st_mtime, tz=local_tz)


class ObjectLastModified(BaseLastModifiedElement):
    """Returns the value of a configurable last modified field on the model instance."""
    view_class = SingleObjectMixin

    def __init__(self, last_modified_field: str = 'modified'):
        self.last_modified_field = last_modified_field

    def value(self, view: SingleObjectMixin) -> Optional[datetime.datetime]:
        obj = view.get_object()
        if not hasattr(view.model, self.last_modified_field):
            raise ImproperlyConfigured(
                f"{view.model} does not have a field named {self.last_modified_field}."
            )
        return getattr(obj, self.last_modified_field)


class QuerySetLastModified(BaseLastModifiedElement):
    """Returns the latest value of a configurable last modified field on the model queryset."""

    view_class = MultipleObjectMixin

    def __init__(self, last_modified_field: str = 'modified'):
        self.last_modified_field = last_modified_field

    def value(self, view: MultipleObjectMixin) -> Optional[datetime.datetime]:
        if not hasattr(view.model, self.last_modified_field):
            raise ImproperlyConfigured(
                f"{view.model} does not have a field named {self.last_modified_field}."
            )
        last_modified = view.get_queryset().order_by('-' + self.last_modified_field) \
            .values_list(self.last_modified_field, flat=True).first()
        return last_modified
