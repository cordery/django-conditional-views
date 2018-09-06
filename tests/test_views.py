from datetime import timedelta

import pytest
from django.utils.http import http_date

from django_conditional_views.elements.etag import RenderedContentEtag
from django_conditional_views.elements.last_modified import ObjectLastModified, \
    QuerySetLastModified, TemplateLastModified
from .conftest import get_etag, last_modified
from .models import ConditionalGetModel


class TestConditionalGetView:

    @pytest.mark.parametrize('elements,value', (
            # Single element
            ([lambda x: last_modified], last_modified),
            # Multiple elements
            (
                    [
                        lambda x: last_modified - timedelta(days=1),
                        lambda x: last_modified,
                        lambda x: last_modified - timedelta(days=2),
                    ],
                    last_modified
            ),
            # No elements
            (None, None),
            # All elements are blank
            ([lambda x: None, lambda x: None], None)
    ))
    def test_get_last_modified(self, test_request, template_view, elements, value):
        """Assert that get_last_modified returns a datetime"""
        template_view.last_modified_elements = elements

        assert value == template_view().get_last_modified()

    @pytest.mark.parametrize('elements,value', (
            # Single element
            ([lambda x, y: 'test_etag'], get_etag('test_etag').strip('"')),
            # Multiple elements
            (
                    [lambda x, y: 'test_etag', lambda x, y: 'test_etag2'],
                    get_etag('test_etagtest_etag2').strip('"')
            ),
            # No elements
            (None, None),
            # All elements are blank
            ([lambda x, y: None, lambda x, y: None], None)
    ))
    def test_get_post_render_etag(self, test_request, template_view, elements, value):
        """Assert that get_post_render_etag returns an etag"""
        template_view.post_render_etag_elements = elements
        response = template_view.as_view()(test_request)
        assert value == template_view().get_post_render_etag(response)

    def test_get_post_render_etag_no_render(self, test_request, base_view):
        """Assert the get_post_render_etag handles a response which has no render method"""
        base_view.post_render_etag_elements = [lambda x, y: 'never_called']
        response = base_view.as_view()(test_request)
        assert None is base_view().get_post_render_etag(response)

    @pytest.mark.parametrize('etag_val,last_modified_val,etag_header,last_modified_header', (
            (None, None, None, None),
            ('test', None, '"test"', None),
            (None, last_modified, None, http_date(last_modified.timestamp())),
            ('test', last_modified, '"test"', http_date(last_modified.timestamp())),
            (None, last_modified.timestamp(), None, http_date(last_modified.timestamp()))
    ))
    def test_set_response_headers(self, test_request, base_view, etag_val, last_modified_val,
                                  etag_header,
                                  last_modified_header):
        response = base_view.as_view()(test_request)
        response = base_view().set_response_headers(response, etag=etag_val,
                                                    last_modified=last_modified_val)
        assert etag_header == response.get('ETag', None)
        assert last_modified_header == response.get('Last-Modified', None)

    @pytest.mark.parametrize('_input,output', (
            (None, None),
            (last_modified, http_date(last_modified.timestamp())),
            (last_modified.timestamp(), http_date(last_modified.timestamp())),
            (int(last_modified.timestamp()), http_date(last_modified.timestamp())),
    ))
    def test_format_last_modified(self, base_view, _input, output):
        assert output == base_view()._format_last_modified(_input)


class TestConditionalGetTemplateViewMixin:

    def test_last_modified_elements(self, conditional_template_view):
        """Assert the expected last modified elements exist"""
        assert TemplateLastModified in conditional_template_view.last_modified_elements

    def test_post_render_etag_elements(self, conditional_template_view):
        """Assert the expected post render etag elements exist"""
        assert RenderedContentEtag in conditional_template_view.post_render_etag_elements


@pytest.mark.django_db
class TestConditionalGetDetailViewMixin:

    def test_last_modified_elements(self, conditional_detail_view):
        """Assert the expected last modified elements exist"""
        ConditionalGetModel.objects.create()
        view = conditional_detail_view(pk=1)
        view.kwargs = {'pk': 1}
        view.get_last_modified()

        assert TemplateLastModified in view.last_modified_elements
        assert any([isinstance(x, ObjectLastModified) for x in
                    view.last_modified_elements])

    def test_post_render_etag_elements(self, conditional_detail_view):
        """Assert the expected post render etag elements exist"""
        assert RenderedContentEtag in conditional_detail_view.post_render_etag_elements


@pytest.mark.django_db
class TestConditionalListDetailViewMixin:

    def test_last_modified_elements(self, conditional_list_view):
        """Assert the expected last modified elements exist"""
        ConditionalGetModel.objects.create()
        view = conditional_list_view()
        view.get_last_modified()

        assert TemplateLastModified in view.last_modified_elements
        assert any([isinstance(x, QuerySetLastModified) for x in
                    view.last_modified_elements])

    def test_post_render_etag_elements(self, conditional_list_view):
        """Assert the expected post render etag elements exist"""
        assert RenderedContentEtag in conditional_list_view.post_render_etag_elements
