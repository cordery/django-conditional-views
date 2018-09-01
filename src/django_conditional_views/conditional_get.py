import hashlib
import os
from calendar import timegm
from datetime import datetime
from typing import ClassVar, Optional, Union

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, HttpResponse
from django.template.loader import select_template
from django.template.response import SimpleTemplateResponse
from django.utils.cache import get_conditional_response
from django.utils.http import http_date, parse_http_date_safe, quote_etag
from django.views.generic import DetailView, ListView
from django.views.generic.base import TemplateResponseMixin, View

__all__ = ['ConditionalGetMixin', 'ConditionalGetTemplateViewMixin',
           'ConditionalGetDetailViewMixin', 'ConditionalGetListViewMixin']


class ConditionalGetMixin(View):
    """Conditional Request/Response aware mixin for View

    If a request is made with conditional request headers, such as HTTP_IF_MODIFIED_SINCE or
    HTTP_IF_NONE_MATCH, the conditional request will be evaluated by
    django.utils.cache.get_conditional_response_.

    If the condition of the request is met then then normal view response will be returned, and the
    Etag and Last-Modified headers will be set if those values could be computed.

    If the condition of the request is NOT met then either a `304 Not Modified`_ or a `412
    Precondition Failed`_ response will be returned instead.

    .. _django.utils.cache.get_conditional_response:
       https://github.com/django/django/blob/master/django/utils/cache.py#L134
    .. _304 Not Modified: https://tools.ietf.org/html/rfc7232#section-4.1
    .. _412 Precondition Failed: https://tools.ietf.org/html/rfc7232#section-4.2
    """

    def get_pre_render_etag(self) -> Optional[str]:
        """Override to derive an Etag before the response is rendered.

        Can potentially save a call to dispatch.

        :return: The calculated etag or ''
        """
        return ''

    def get_last_modified(self) -> Optional[datetime]:
        """Override to derive a Last-Modified datetime.

        Can potentially save a call to dispatch.

        :return: A datetime representing the last time the view content was modified, or None.
        """
        return None

    def set_response_headers(self, response: SimpleTemplateResponse, etag: str = None,
                             last_modified: Union[int, datetime] = None) -> SimpleTemplateResponse:
        """Sets the Etag and Last-Modified headers on the response

        Override if you want to change the final headers.

        :param response: The response to add the headers to.
        :param etag: The properly formatted etag to add to the header.
        :param last_modified: The datetime or timestamp integer to set as the last_modified date.
        :return: The response with the headers added.
        """
        if etag:
            response['Etag'] = etag

        if last_modified:
            if isinstance(last_modified, int):
                last_modified = http_date(last_modified)
            response['Last-Modified'] = last_modified
        return response

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Conditional Request/Response aware wrapper for dispatch.

        Calls get_last_modified and get_pre_render_etag to compute the Last-Modified and Etag
        headers, and then compares those against the conditional request headers (if any) to
        determine whether to return a 304 or 412 response.

        If a 304 or 412 response will be sent the super().dispatch method will never be called,
        so any computation or side effects done there will not happen.

        If not, the original response will
        be returned along with Etag and Last-Modified headers if those values were returned by
        get_last_modified and get_pre_render_etag.
        """
        last_modified = self._get_last_modified()

        # Try to get an etag from the pre_render_etag method
        etag = self._prepare_etag(self.get_pre_render_etag())
        conditional_response = self._get_conditional_response(request, etag,
                                                              last_modified)
        if conditional_response:
            # Return an abbreviated conditional response instead of proceeding with
            #  dispatch.
            return conditional_response

        response = super().dispatch(request, *args, **kwargs)

        return self.set_response_headers(response, etag=etag, last_modified=last_modified)

    def _get_conditional_response(self, request, etag, last_modified):
        """Mimics ConditionalGetMiddleware"""
        return get_conditional_response(
            request,
            etag=etag,
            last_modified=last_modified,
        )

    def _prepare_etag(self, etag):
        """Formats the results of get_post_render_etag"""
        self._etag = etag
        if not etag:
            return None
        return quote_etag(etag)

    def _get_last_modified(self):
        """Formats the results of get_last_modified"""
        res_last_modified = self.get_last_modified()
        if res_last_modified:
            res_last_modified = timegm(res_last_modified.utctimetuple())
        return res_last_modified


class ConditionalGetTemplateViewMixin(TemplateResponseMixin, ConditionalGetMixin):
    """
    Conditional Request/Response aware mixin for TemplateView

    Builds on ConditionalGetViewMixin further adding the following:
    * By default, Last modified will be automatically set to the last modified timestamp of the
    template file.
    * A new method has been added -- get_post_render_etag -- that provides a way to derive the
    etag from the rendered response.  By default, this method hashes the response.content to
    derive the etag.
    """

    def get_template_last_modified(self) -> datetime:
        """Stats the template file to get the last modified time."""
        t = select_template(self.get_template_names())
        local_tz = datetime.now().astimezone().tzinfo
        return datetime.fromtimestamp(os.stat(t.origin.name).st_mtime,
                                      tz=local_tz)

    def get_last_modified(self) -> datetime:
        """Calls self.get_template_last_modified()"""
        return self.get_template_last_modified()

    def get_post_render_etag(self, response: SimpleTemplateResponse) -> str:
        """Override to derive an etag after the response was rendered.

        No time is saved except the time it would take to transmit the request.

        :param response: A response on which the .render() method has already been called.
        :return: the etag string
        """
        return hashlib.md5(response.content).hexdigest()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        response = super().dispatch(request, *args, *kwargs)
        if not isinstance(response, SimpleTemplateResponse):
            return response
        last_modified = parse_http_date_safe(response.get('Last-Modified'))
        etag = response.get('Etag', None)
        # If we do not yet have an etag, try to get one from the post_render_etag method
        if not etag and not response.streaming:
            response = response.render()
            etag = self._prepare_etag(self.get_post_render_etag(response))

        conditional_response = self._get_conditional_response(request, etag,
                                                              last_modified)
        if conditional_response:
            return conditional_response
        # Finally set the Etag headers if required and return the
        # response
        return self.set_response_headers(response, etag=etag)


class ConditionalGetDetailViewMixin(ConditionalGetTemplateViewMixin, DetailView):
    """Conditional Request/Response aware mixin for DetailView

    Builds on ConditionalGetTemplateViewMixin further adding the following:
    * a configurable last_modified_field class property with which you can name which field on
    the model
    should be used to find the last modified date.
    * By default, Last modified will return the contents of the last_modified_field from the
    model instance.

    """
    last_modified_field: ClassVar[str] = 'modified'

    def get_last_modified(self) -> Optional[datetime]:
        """Returns the value of last_modified_field on the model instance."""
        self.object = self.get_object()
        if not hasattr(self.model, self.last_modified_field):
            raise ImproperlyConfigured(
                f"{self.model} does not have a field named {self.last_modified_field}.  Update "
                f"your view definition and set the last_modified_field property"
            )
        last_modified = getattr(self.object, self.last_modified_field)
        if last_modified:
            return max(last_modified, self.get_template_last_modified())
        return None

    def get_object(self, queryset=None):
        """Wraps get_object to use the existing object if it has already been retrieved."""
        if hasattr(self, 'object') and self.object:
            return self.object
        return super().get_object(queryset=queryset)


class ConditionalGetListViewMixin(ConditionalGetTemplateViewMixin, ListView):
    """Conditional Request/Response aware mixin for ListView

       Builds on ConditionalGetTemplateViewMixin further adding the following:
       * a configurable last_modified_field class property with which you can name which field on
       the model should be used to find the last modified date.
       * By default, Last modified will be the latest value of last_modified_field in the queryset.

       """
    last_modified_field: ClassVar[str] = 'modified'

    def get_last_modified(self) -> Optional[datetime]:
        self.object_list = self.get_queryset()
        if not hasattr(self.model, self.last_modified_field):
            raise ImproperlyConfigured(
                f"{self.model} does not have a field named {self.last_modified_field}.  Update "
                f"your view definition and set the last_modified_field property"
            )
        last_modified = self.get_queryset().order_by('-' + self.last_modified_field) \
            .values_list(self.last_modified_field, flat=True).first()
        if last_modified:
            return max(last_modified, self.get_template_last_modified())
        return None
