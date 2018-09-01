from datetime import datetime
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import _engine_list
from django.utils.http import http_date
from pytz import UTC

from django_conditional_views import __version__
from .models import ConditionalGetModel
from .views import AlternativeModifiedDetailView, AlternativeModifiedListView, PostRenderView, \
    SimpleDetailView, SimpleEtagView, SimpleLastModifiedView, SimpleListView, SimpleView


def test_version():
    assert __version__ == '0.1.0'


class TestConditionalGetMixin:
    last_modified = datetime(2018, 1, 1, 0, 0, 0, tzinfo=UTC)

    def test_default(self, rf):
        request = rf.get('/test')
        response = SimpleView.as_view()(request)
        assert 200 == response.status_code
        assert 'Etag' not in response
        assert 'Last-Modified' not in response

    def test_etag(self, rf):
        request = rf.get('/test')
        response = SimpleEtagView.as_view()(request)
        assert 200 == response.status_code
        assert '"test_etag"' == response['Etag']
        assert 'Last-Modified' not in response

    def test_last_modified(self, rf, last_modified):
        request = rf.get('/test')
        response = SimpleLastModifiedView.as_view()(request)
        assert 200 == response.status_code
        assert not response.get('Etag', None)
        assert http_date(last_modified.timestamp()) \
               == response['Last-Modified']

    def test_conditional_response_etag(self, rf, last_modified):
        request = rf.get('/test', HTTP_IF_NONE_MATCH='"test_etag"')
        response = SimpleEtagView.as_view()(request)
        assert 304 == response.status_code

    def test_conditional_response_last_modified(self, rf, last_modified):
        request = rf.get(
            '/test',
            HTTP_IF_MODIFIED_SINCE=http_date(last_modified.timestamp())
        )
        response = SimpleLastModifiedView.as_view()(request)
        assert 304 == response.status_code


class TestConditionalGetTemplateViewMixin:
    def test_default(self, test_request, local_tz, get_etag, template_on_disk):
        response = PostRenderView.as_view()(test_request)

        path = Path(template_on_disk)
        assert 200 == response.status_code
        assert b'' == response.content
        assert get_etag("") == response['Etag']

        last_modified = datetime.fromtimestamp(path.stat().st_mtime, tz=local_tz)
        assert http_date(last_modified.timestamp()) == response['Last-Modified']

        # Modify the file
        with open(template_on_disk, 'w') as fp:
            fp.write('Test')

        # This line is required to force django.template.loaders.filesystem.Loader to
        # reload the template.
        _engine_list()[0].engine.template_loaders[0].reset()

        last_modified2 = datetime.fromtimestamp(path.stat().st_mtime, tz=local_tz)
        assert last_modified != last_modified2

        response = PostRenderView.as_view()(test_request)
        assert 200 == response.status_code
        assert b'Test' == response.content
        assert get_etag("Test") == response['Etag']

        assert http_date(last_modified2.timestamp()) == response['Last-Modified']

    def test_conditional_response_etag(self, rf, get_etag, template_on_disk):
        request = rf.get('/test', HTTP_IF_NONE_MATCH=get_etag(""))
        response = PostRenderView.as_view()(request)
        assert 304 == response.status_code

    def test_conditional_response_last_modified(self, rf, template_on_disk, local_tz):
        last_modified = datetime.fromtimestamp(Path(template_on_disk).stat().st_mtime, tz=local_tz)
        request = rf.get(
            '/test',
            HTTP_IF_MODIFIED_SINCE=http_date(last_modified.timestamp())
        )
        response = PostRenderView.as_view()(request)
        assert 304 == response.status_code


@pytest.mark.django_db
class TestConditionalGetDetailViewMixin:
    def test_default(self, test_request, template_on_disk, local_tz, get_etag):
        SimpleDetailView.template_name = template_on_disk
        with open(template_on_disk, 'w') as fp:
            fp.write('{{object.value}}')

        obj = ConditionalGetModel.objects.create(value="Test 1")

        response = SimpleDetailView.as_view()(test_request, pk=1)
        assert 200 == response.status_code
        assert get_etag("Test 1") == response['Etag']
        assert http_date(obj.modified.timestamp()) == response['Last-Modified']

        obj.value = "Test 2"
        obj.save()

        response = SimpleDetailView.as_view()(test_request, pk=1)
        assert 200 == response.status_code
        assert get_etag("Test 2") == response['Etag']
        assert http_date(obj.modified.timestamp()) == response['Last-Modified']

    def test_modified_field(self, test_request, template_on_disk, local_tz, get_etag):
        AlternativeModifiedDetailView.template_name = template_on_disk
        obj = ConditionalGetModel.objects.create(
            alternative_modified=datetime(2020, 1, 1, 0, 0, 0, tzinfo=local_tz))

        response = AlternativeModifiedDetailView.as_view()(test_request, pk=1)
        assert 200 == response.status_code
        assert get_etag("") == response['Etag']
        assert http_date(obj.alternative_modified.timestamp()) == response['Last-Modified']

    def test_blank_modified_field(self, test_request, template_on_disk, local_tz, get_etag):
        AlternativeModifiedDetailView.template_name = template_on_disk
        AlternativeModifiedDetailView.last_modified_field = 'value'
        ConditionalGetModel.objects.create()

        response = AlternativeModifiedDetailView.as_view()(test_request, pk=1)
        assert 200 == response.status_code
        assert get_etag("") == response['Etag']
        assert 'Last-Modified' not in response

    def test_invalid_config(self, test_request, template_on_disk, local_tz):
        AlternativeModifiedDetailView.template_name = template_on_disk
        AlternativeModifiedDetailView.last_modified_field = 'does_not_exist'
        ConditionalGetModel.objects.create(
            alternative_modified=datetime(2020, 1, 1, 0, 0, 0, tzinfo=local_tz))

        with pytest.raises(ImproperlyConfigured):
            AlternativeModifiedDetailView.as_view()(test_request, pk=1)


@pytest.mark.django_db
class TestConditionalListDetailViewMixin:
    def test_last_modified_changes_on_create(self, test_request, template_on_disk, local_tz,
                                             get_etag):
        SimpleListView.template_name = template_on_disk

        obj = ConditionalGetModel.objects.create()

        response = SimpleListView.as_view()(test_request)
        assert 200 == response.status_code
        assert http_date(obj.modified.timestamp()) == response['Last-Modified']

        obj = ConditionalGetModel.objects.create()

        response = SimpleListView.as_view()(test_request, pk=1)
        assert 200 == response.status_code
        assert http_date(obj.modified.timestamp()) == response['Last-Modified']

    def test_last_modified_changes_on_modified(self, test_request, template_on_disk, local_tz,
                                               get_etag):
        SimpleListView.template_name = template_on_disk

        obj = ConditionalGetModel.objects.create()

        response = SimpleListView.as_view()(test_request)
        assert 200 == response.status_code
        assert http_date(obj.modified.timestamp()) == response['Last-Modified']

        obj.last_modified = datetime(2020, 1, 1, 0, 0, 0, tzinfo=local_tz)
        obj.save()

        response = SimpleListView.as_view()(test_request, pk=1)
        assert 200 == response.status_code
        assert http_date(obj.modified.timestamp()) == response['Last-Modified']

    def test_etag_changes(self, test_request, template_on_disk, local_tz, get_etag):
        SimpleListView.template_name = template_on_disk
        with open(template_on_disk, 'w') as fp:
            fp.write('{{object_list.count}}')

        ConditionalGetModel.objects.create()

        response = SimpleListView.as_view()(test_request)
        assert 200 == response.status_code
        assert get_etag("1") == response['Etag']

        ConditionalGetModel.objects.create()

        response = SimpleListView.as_view()(test_request)
        assert 200 == response.status_code
        assert get_etag("2") == response['Etag']

    def test_modified_field(self, test_request, template_on_disk, local_tz, get_etag):
        AlternativeModifiedListView.template_name = template_on_disk
        obj = ConditionalGetModel.objects.create(
            alternative_modified=datetime(2020, 1, 1, 0, 0, 0, tzinfo=local_tz))

        response = AlternativeModifiedListView.as_view()(test_request)
        assert 200 == response.status_code
        assert get_etag("") == response['Etag']
        assert http_date(obj.alternative_modified.timestamp()) == response['Last-Modified']

    def test_invalid_config(self, test_request, template_on_disk):
        AlternativeModifiedListView.template_name = template_on_disk
        AlternativeModifiedListView.last_modified_field = 'does_not_exist'
        with pytest.raises(ImproperlyConfigured):
            AlternativeModifiedListView.as_view()(test_request)

    def test_empty_queryset(self, test_request, template_on_disk, local_tz, get_etag):
        SimpleListView.template_name = template_on_disk
        response = SimpleListView.as_view()(test_request)
        assert 200 == response.status_code
        assert get_etag("") == response['Etag']
        assert 'Last-Modified' not in response
