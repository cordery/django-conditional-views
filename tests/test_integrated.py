from datetime import datetime
from pathlib import Path

import pytest
from django.utils import timezone
from django.utils.http import http_date
from pytz import UTC

from django_conditional_views import __version__
from .conftest import get_etag, last_modified
from .models import ConditionalGetModel


def test_version():
    assert __version__ == '0.1.3'


class TestConditionalGetMixin:
    last_modified = datetime(2018, 1, 1, 0, 0, 0, tzinfo=UTC)

    def test_default(self, test_request, base_view):
        """Assert that including the base mixin does not generate any headers by default"""
        response = base_view.as_view()(test_request)
        assert 200 == response.status_code
        assert 'ETag' not in response
        assert 'Last-Modified' not in response

    def test_last_modified(self, test_request, base_view):
        base_view.last_modified_elements = [lambda x: last_modified]
        response = base_view.as_view()(test_request)
        assert 200 == response.status_code
        assert http_date(last_modified.timestamp()) == response['Last-Modified']

    def test_pre_rendered_etag(self, test_request, base_view):
        base_view.pre_render_etag_elements = [lambda x: 'test_etag']
        response = base_view.as_view()(test_request)
        assert 200 == response.status_code
        assert get_etag('test_etag') == response['ETag']

    def test_post_rendered_etag(self, test_request, template_view):
        template_view.post_render_etag_elements = [lambda x, y: 'test_etag']
        response = template_view.as_view()(test_request).render()
        assert 200 == response.status_code
        assert get_etag('test_etag') == response['ETag']

    def test_get_post_render_etag_streaming(self, test_request, template_view):
        """Assert the get_post_render_etag handles a response which is streaming"""
        template_view.post_render_etag_elements = [lambda x, y: 'test_etag']
        response = template_view.as_view()(test_request)
        response.streaming = True
        response.render()
        assert 200 == response.status_code
        assert 'Etag' not in response

    def test_conditional_response_etag(self, rf, base_view):
        base_view.pre_render_etag_elements = [lambda x: 'test_etag']
        request = rf.get('/test', HTTP_IF_NONE_MATCH=get_etag('test_etag'))
        response = base_view.as_view()(request)
        assert 304 == response.status_code

    def test_conditional_response_last_modified(self, rf, base_view):
        base_view.last_modified_elements = [lambda x: last_modified]
        request = rf.get(
            '/test',
            HTTP_IF_MODIFIED_SINCE=http_date(last_modified.timestamp())
        )
        response = base_view.as_view()(request)
        assert 304 == response.status_code


class TestConditionalGetTemplateViewMixin:

    def test_conditional_response_etag(self, rf, conditional_template_view):
        request = rf.get('/test', HTTP_IF_NONE_MATCH=get_etag("Test"))
        response = conditional_template_view.as_view()(request).render()
        assert 304 == response.status_code

    def test_conditional_response_last_modified(self, rf, conditional_template_view,
                                                template_on_disk, local_tz):
        last_modified = datetime.fromtimestamp(Path(template_on_disk).stat().st_mtime, tz=local_tz)
        request = rf.get(
            '/test',
            HTTP_IF_MODIFIED_SINCE=http_date(last_modified.timestamp())
        )
        response = conditional_template_view.as_view()(request)
        assert 304 == response.status_code


@pytest.mark.django_db
class TestConditionalGetDetailViewMixin:

    def test_default(self, test_request, conditional_detail_view, template_on_disk, local_tz):
        with open(template_on_disk, 'w') as fp:
            fp.write('{{object.value}}')

        obj = ConditionalGetModel.objects.create(value="Test 1")

        response = conditional_detail_view.as_view()(test_request, pk=1).render()
        assert 200 == response.status_code
        assert get_etag("Test 1") == response['ETag']
        assert http_date(obj.modified.timestamp()) == response['Last-Modified']

        obj.value = "Test 2"
        obj.save()

        response = conditional_detail_view.as_view()(test_request, pk=1).render()
        assert 200 == response.status_code
        assert get_etag("Test 2") == response['ETag']
        assert http_date(obj.modified.timestamp()) == response['Last-Modified']

    def test_modified_field(self, test_request, conditional_detail_view, local_tz):
        conditional_detail_view.last_modified_field = 'alternative_modified'
        alt_timestamp = timezone.now()
        obj = ConditionalGetModel.objects.create(alternative_modified=alt_timestamp)

        response = conditional_detail_view.as_view()(test_request, pk=1).render()
        assert 200 == response.status_code
        assert get_etag("Test") == response['ETag']
        assert http_date(obj.alternative_modified.timestamp()) == response['Last-Modified']


@pytest.mark.django_db
class TestConditionalListDetailViewMixin:

    def test_last_modified_changes_on_create(self, test_request, conditional_list_view, local_tz):
        obj = ConditionalGetModel.objects.create()

        response = conditional_list_view.as_view()(test_request)
        assert 200 == response.status_code
        assert http_date(obj.modified.timestamp()) == response['Last-Modified']

        obj = ConditionalGetModel.objects.create()

        response = conditional_list_view.as_view()(test_request, pk=1)
        assert 200 == response.status_code
        assert http_date(obj.modified.timestamp()) == response['Last-Modified']

    def test_last_modified_changes_on_modified(self, test_request, conditional_list_view,
                                               local_tz):
        obj = ConditionalGetModel.objects.create()

        response = conditional_list_view.as_view()(test_request)
        assert 200 == response.status_code
        assert http_date(obj.modified.timestamp()) == response['Last-Modified']

        obj.last_modified = datetime(2020, 1, 1, 0, 0, 0, tzinfo=local_tz)
        obj.save()

        response = conditional_list_view.as_view()(test_request, pk=1)
        assert 200 == response.status_code
        assert http_date(obj.modified.timestamp()) == response['Last-Modified']

    def test_etag_changes(self, test_request, conditional_list_view, template_on_disk, local_tz):
        with open(template_on_disk, 'w') as fp:
            fp.write('{{object_list.count}}')

        ConditionalGetModel.objects.create()

        response = conditional_list_view.as_view()(test_request).render()
        assert 200 == response.status_code
        assert get_etag("1") == response['ETag']

        ConditionalGetModel.objects.create()

        response = conditional_list_view.as_view()(test_request).render()
        assert 200 == response.status_code
        assert get_etag("2") == response['ETag']

    def test_modified_field(self, test_request, conditional_list_view, local_tz):
        obj = ConditionalGetModel.objects.create(
            alternative_modified=datetime(2020, 1, 1, 0, 0, 0, tzinfo=local_tz))

        conditional_list_view.last_modified_field = 'alternative_modified'

        response = conditional_list_view.as_view()(test_request).render()
        assert 200 == response.status_code
        assert get_etag("Test") == response['ETag']
        assert http_date(obj.alternative_modified.timestamp()) == response['Last-Modified']

    def test_empty_queryset(self, test_request, template_on_disk, conditional_list_view, local_tz):
        response = conditional_list_view.as_view()(test_request).render()
        assert 200 == response.status_code
        assert get_etag("Test") == response['ETag']
        assert http_date(Path(template_on_disk).stat().st_mtime) == response['Last-Modified']
