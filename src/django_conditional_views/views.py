import hashlib
from calendar import timegm
from datetime import datetime
from functools import partial
from typing import ClassVar, Optional, Type, Union

from django.http import HttpRequest, HttpResponse
from django.template.response import SimpleTemplateResponse
from django.utils.cache import get_conditional_response
from django.utils.http import http_date, quote_etag
from django.views.generic import DetailView, ListView
from django.views.generic.base import TemplateResponseMixin, View

from .elements.base import BaseElement
from .elements.etag import RenderedContentEtag
from .elements.last_modified import ObjectLastModified, QuerySetLastModified, TemplateLastModified
from .helpers import instantiate

__all__ = ['ConditionalGetMixin', 'ConditionalGetTemplateViewMixin',
           'ConditionalGetDetailViewMixin', 'ConditionalGetListViewMixin']


class ConditionalGetMixin(View):
    # language=rst prefix="    "
    """Conditional Request/Response aware mixin for View

    If a request is made with conditional request headers, such as If-Modified-Since_ or
    If-None-Match_, the conditional request will be evaluated by
    `django.utils.cache.get_conditional_response`_.

    If the condition of the request is met then then normal view response will be returned, and the
    Etag and Last-Modified headers will be set if those values could be computed.

    If the condition of the request is NOT met then either a `304 Not Modified`_ or
    a `412 Precondition Failed`_ response will be returned instead.

    .. _If-Modified-Since:
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/If-Modified-Since
    .. _If-None-Match:
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/If-None-Match
    .. _django.utils.cache.get_conditional_response:
        https://github.com/django/django/blob/master/django/utils/cache.py#L134
    .. _304 Not Modified: https://tools.ietf.org/html/rfc7232#section-4.1
    .. _412 Precondition Failed: https://tools.ietf.org/html/rfc7232#section-4.2

    """

    last_modified_elements: ClassVar[Union[BaseElement, Type[BaseElement]]] = None
    pre_render_etag_elements: ClassVar[Union[BaseElement, Type[BaseElement]]] = None
    post_render_etag_elements: ClassVar[Union[BaseElement, Type[BaseElement]]] = None

    def get_last_modified(self) -> Optional[datetime]:
        # language=rst prefix="    "
        """Derive a Last-Modified datetime for the view.

        Can potentially save a call to dispatch.

        :return: A datetime representing the last time the view content was modified, or None.
        """
        if not self.last_modified_elements:
            return None

        elements = [x(self) for x in instantiate(self.last_modified_elements)]
        elements = [x for x in elements if x]
        if not elements:
            return None

        return max(elements)

    def get_pre_render_etag(self) -> Optional[str]:
        # language=rst prefix="    "
        """Derive an ETag before the response is rendered.

        Can potentially save a call to dispatch.

        :return: The calculated ETag or ''
        """
        if not self.pre_render_etag_elements:
            return None

        elements = [x(self) for x in instantiate(self.pre_render_etag_elements)]
        return self._render_etag_elements(elements)

    def get_post_render_etag(self, response: SimpleTemplateResponse) -> Optional[str]:
        # language=rst prefix="    "
        """Derive an Etag after the response is rendered.

        :return: The calculated ETag or None
        """
        if not self.post_render_etag_elements:
            return None

        if not hasattr(response, 'render'):
            return None

        # Render the response
        response.render()

        elements = [x(self, response) for x in instantiate(self.post_render_etag_elements)]
        return self._render_etag_elements(elements)

    @staticmethod
    def _render_etag_elements(elements):
        elements = [x for x in elements if x]
        elements = [x.encode() if isinstance(x, str) else x for x in elements]
        if not elements:
            return None
        return hashlib.md5(b''.join(elements)).hexdigest()

    def set_response_headers(self, response: SimpleTemplateResponse,
                             etag: str = None,
                             last_modified: Union[int, float, datetime] = None
                             ) -> SimpleTemplateResponse:
        # language=rst prefix="    "
        """Sets the Etag and Last-Modified headers on the response

        Override if you want to change the final headers.

        :param response: The response to add the headers to.
        :param etag: The properly formatted etag to add to the header.
        :param last_modified: The datetime or timestamp integer to set as the last_modified date.
        :return: The response with the headers added.
        """
        if etag:
            response['Etag'] = self._format_etag(etag)

        if last_modified:
            response['Last-Modified'] = self._format_last_modified(last_modified)
        return response

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        # language=rst prefix="    "
        """Conditional Request/Response aware wrapper for dispatch.

        Calls get_last_modified and get_pre_render_etag to compute the Last-Modified and Etag
        headers, and then compares those against the conditional request headers (if any) to
        determine whether to return a 304 or 412 response.

        If a 304 or 412 response will be sent the super().dispatch method will never be called,
        so any computation or side effects done there will not happen.

        Otherwise, the response will be rendered and get_post_render_etag will be called to try to
        get a post_render etag.  Once again this will be compared against any conditional request
        headers to determine whether to send a 304 or 412 response.

        If no conditional response will be sent, the Last-Modified and Etag headers for the
        current response are set and the response is returned.
        """
        last_modified = self._prep_last_modified(self.get_last_modified())

        # 1. Try to get an etag from the pre_render_etag method
        etag = self._prep_etag(self.get_pre_render_etag())

        # 2. Try to generate a conditional response given the last_modified and pre_render_etag.
        # If possible, return an abbreviated conditional response using the last_modified and
        # pre_render_etag instead of proceeding with dispatch.
        conditional_response = self._get_conditional_response(request, etag, last_modified)
        if conditional_response:
            return conditional_response

        # 3. call the super dispatch
        response = super().dispatch(request, *args, **kwargs)
        response = self.set_response_headers(response, etag=etag, last_modified=last_modified)

        # 4. Add a post render callback for post render etag generation
        if hasattr(response, 'add_post_render_callback'):
            response.add_post_render_callback(
                partial(self._post_render_callback, request, last_modified)
            )

        return response

    def _post_render_callback(self, request, last_modified, response):
        # 1. If we do not yet have an etag, try to get one from the post_render_etag method
        etag = response.get('ETag')
        if not etag and not response.streaming:
            etag = self._format_etag(self.get_post_render_etag(response))

        # 2. Once again try to generate a conditional response given the last_modified and
        # pre_render_etag.
        conditional_response = self._get_conditional_response(request, etag,
                                                              last_modified)
        if conditional_response:
            return conditional_response

        # 3. Finally set the Etag headers
        response = self.set_response_headers(response, etag=etag, last_modified=last_modified)
        return response

    def _get_conditional_response(self, request, etag, last_modified):
        """Mimics ConditionalGetMiddleware"""
        return get_conditional_response(
            request,
            etag=etag,
            last_modified=last_modified,
        )

    def _prep_etag(self, etag: Optional[str]):
        """Prep etag for the conditional check phase"""
        return self._format_etag(etag)

    @staticmethod
    def _format_etag(etag: Optional[str]):
        """Format etag for the http header"""
        if not etag:
            return None
        return quote_etag(etag)

    @staticmethod
    def _prep_last_modified(last_modified: Optional[datetime]):
        """Prep last_modified for the conditional check phase"""
        if not last_modified:
            return None
        return timegm(last_modified.utctimetuple())

    def _format_last_modified(self, last_modified: Union[int, float, datetime, None]):
        """Format the results of get_last_modified for the http header"""
        if not last_modified:
            return None
        if isinstance(last_modified, datetime):
            last_modified = self._prep_last_modified(last_modified)
        return http_date(last_modified)


class ConditionalGetTemplateViewMixin(TemplateResponseMixin, ConditionalGetMixin):
    # language=rst prefix="    "
    """
    Conditional Request/Response aware mixin for TemplateView

    *Last-Modified:*  Calculated from the the template last modified timestamp.

    *Etag:* Calculated from the rendered response.
    """
    last_modified_elements = [TemplateLastModified]
    post_render_etag_elements = [RenderedContentEtag]


class ConditionalGetDetailViewMixin(ConditionalGetMixin, DetailView):
    # language=rst prefix="    "
    """Conditional Request/Response aware mixin for DetailView

    *Last-Modified:*  Calculated from the latest of the template last modified timestamp and a
    configurable field on the model object, default 'modified'.

    *Etag:* Calculated from the rendered response.
    """
    last_modified_field: ClassVar[str] = 'modified'

    post_render_etag_elements = [RenderedContentEtag]

    def get_last_modified(self):
        # TemplateLastModified requires that object exist
        self.object = super().get_object()
        self.last_modified_elements = self.last_modified_elements or []
        self.last_modified_elements.extend([TemplateLastModified,
                                            ObjectLastModified(self.last_modified_field)])
        return super().get_last_modified()


class ConditionalGetListViewMixin(ConditionalGetMixin, ListView):
    # language=rst prefix="    "
    """Conditional Request/Response aware mixin for ListView

    *Last-Modified:*  Calculated from the latest of the template last modified timestamp and the
    model objects 'modified' field.

    *Etag:* Calculated from the rendered response.
    """
    last_modified_field: ClassVar[str] = 'modified'
    post_render_etag_elements = [RenderedContentEtag]

    def get_last_modified(self):
        # TemplateLastModified requires that object_list exist
        self.object_list = super().get_queryset()
        self.last_modified_elements = self.last_modified_elements or []
        self.last_modified_elements.extend([TemplateLastModified,
                                            QuerySetLastModified(self.last_modified_field)])
        return super().get_last_modified()
