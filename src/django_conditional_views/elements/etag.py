from typing import Optional

from django.template.response import SimpleTemplateResponse
from django.views.generic.base import TemplateResponseMixin

from .base import BaseEtagPostRenderElement

__all__ = ['RenderedContentEtag']


class RenderedContentEtag(BaseEtagPostRenderElement):
    """Returns the response.content to use for etag hashing."""
    view_class = TemplateResponseMixin

    def value(self, view: TemplateResponseMixin,
              response: SimpleTemplateResponse) -> Optional[str]:
        if not response.is_rendered:
            response.render()
        return response.content
