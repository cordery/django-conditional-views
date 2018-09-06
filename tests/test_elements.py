from datetime import datetime
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import _engine_list
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from django_conditional_views.elements.etag import RenderedContentEtag
from django_conditional_views.elements.last_modified import ObjectLastModified, \
    QuerySetLastModified, TemplateLastModified
from .models import ConditionalGetModel


class TestRenderedContentETag:
    def test_type_check(self):
        """Assert that RenderedContentEtag raises an error if not used with a TemplateView"""
        with pytest.raises(ValueError):
            RenderedContentEtag()(View())

    def test_call(self, test_request, template_view, template_on_disk):
        """Assert that RenderedContentEtag returns the rendered content of the response"""

        response = template_view.as_view()(test_request)
        assert b"Test" == RenderedContentEtag()(template_view(), response)

        # Modify the file
        with open(template_on_disk, 'w') as fp:
            fp.write('Test 2')

        response = template_view.as_view()(test_request)
        assert b"Test" == RenderedContentEtag()(template_view(), response)


class TestTemplateLastModified:
    def test_type_check(self):
        """Assert that TemplateLastModified raises an error if not used with a TemplateView"""
        with pytest.raises(ValueError):
            TemplateLastModified()(View())

    def test_call(self, template_on_disk, template_view, local_tz):
        """Assert that TemplateLastModified returns the last modified timestamp of the template"""

        path = Path(template_on_disk)
        last_modified = datetime.fromtimestamp(path.stat().st_mtime, tz=local_tz)
        assert last_modified == TemplateLastModified()(template_view())

        # Modify the file
        path.touch()

        # This line is required to force django.template.loaders.filesystem.Loader to
        # reload the template.
        _engine_list()[0].engine.template_loaders[0].reset()

        last_modified2 = datetime.fromtimestamp(path.stat().st_mtime, tz=local_tz)
        assert last_modified != last_modified2
        assert last_modified2 == TemplateLastModified()(template_view())


@pytest.mark.django_db
class TestObjectLastModified:
    def test_type_check(self):
        """Assert that TemplateLastModified raises an error if not used with a TemplateView"""
        with pytest.raises(ValueError):
            ObjectLastModified()(TemplateView())
        with pytest.raises(ValueError):
            ObjectLastModified()(ListView())

    def test_call(self, detail_view):
        """Assert that ObjectLastModified returns the modified field from the object"""

        obj = ConditionalGetModel.objects.create(value="Test 1")

        view = detail_view(pk=1)
        view.kwargs = {'pk': 1}

        assert obj.modified == ObjectLastModified()(view)

        # modify the object
        obj.value = "Test 2"
        obj.save()

        assert obj.modified == ObjectLastModified()(view)

    def test_modified_field(self, detail_view, local_tz):
        """Assert that ObjectLastModified returns the modified field from the object"""

        obj = ConditionalGetModel.objects.create(alternative_modified=datetime(2000, 1, 1, 1, 1, 1,
                                                                               tzinfo=local_tz))
        view = detail_view(pk=1)
        view.kwargs = {'pk': 1}

        assert obj.alternative_modified == ObjectLastModified('alternative_modified')(view)

        # modify the object
        obj.alternative_modified = datetime(2020, 1, 1, 1, 1, 1, tzinfo=local_tz)
        obj.save()

        assert obj.alternative_modified == ObjectLastModified('alternative_modified')(view)

    def test_blank_modified_field(self, detail_view):
        """Assert that a blank value is returned successfully"""
        ConditionalGetModel.objects.create()
        view = detail_view(pk=1)
        view.kwargs = {'pk': 1}

        assert not ObjectLastModified('alternative_modified')(view)

    def test_invalid_config(self, detail_view):
        """Assert that a non existing field raises an error"""
        ConditionalGetModel.objects.create()
        view = detail_view(pk=1)
        view.kwargs = {'pk': 1}
        with pytest.raises(ImproperlyConfigured):
            ObjectLastModified('invalid_field')(view)


@pytest.mark.django_db
class TestQuerySetLastModified:
    def test_type_check(self):
        """Assert that TemplateLastModified raises an error if not used with a TemplateView"""
        with pytest.raises(ValueError):
            QuerySetLastModified()(TemplateView())
        with pytest.raises(ValueError):
            QuerySetLastModified()(DetailView())

    def test_call(self, list_view):
        """Assert that ObjectLastModified returns the modified field from the object"""

        obj1 = ConditionalGetModel.objects.create(value='Test 1')

        view = list_view()
        assert obj1.modified == QuerySetLastModified()(view)

        obj2 = ConditionalGetModel.objects.create()

        assert obj2.modified == QuerySetLastModified()(view)

        # modify the object
        obj1.value = "Test 2"
        obj1.save()

        assert obj1.modified == QuerySetLastModified()(view)

    def test_modified_field(self, local_tz, list_view):
        """Assert that ObjectLastModified returns the modified field from the object"""

        obj = ConditionalGetModel.objects.create(alternative_modified=datetime(2000, 1, 1, 1, 1, 1,
                                                                               tzinfo=local_tz))

        assert obj.alternative_modified == QuerySetLastModified('alternative_modified')(
            list_view())

    def test_blank_modified_field(self, list_view):
        """Assert that a blank value is returned successfully"""
        ConditionalGetModel.objects.create()
        assert None is QuerySetLastModified('alternative_modified')(list_view())

    def test_invalid_config(self, list_view):
        """Assert that a non existing field raises an error"""
        with pytest.raises(ImproperlyConfigured):
            QuerySetLastModified('invalid_field')(list_view())
