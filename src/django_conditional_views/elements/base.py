import datetime
from abc import ABC
from typing import Optional

from django.template.response import SimpleTemplateResponse


class BaseElement(ABC):
    """Base class for classes that derive either Last-Modified or Etag from the view."""
    view_class = None

    def value(self, *args, **kwargs):
        raise NotImplementedError

    def __call__(self, view, *args, **kwargs):
        if not isinstance(view, self.view_class):
            raise ValueError(f'This function is only compatible with {self.view_class} views.')
        return self.value(view, *args, **kwargs)


class BaseLastModifiedElement(BaseElement, ABC):
    """Inherit to define an element that derives Last-Modified"""

    def value(self, view) -> Optional[datetime.datetime]:
        raise NotImplementedError


class BasePreRenderEtagElement(BaseElement, ABC):
    """Inherit to define an element that derives a pre render ETag"""

    def value(self, view) -> Optional[str]:
        raise NotImplementedError


class BaseEtagPostRenderElement(BaseElement, ABC):
    """Inherit to define an element that derives a post render ETag"""

    def value(self, view, response: SimpleTemplateResponse) -> Optional[str]:
        raise NotImplementedError
