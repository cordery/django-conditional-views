import hashlib
import os
from datetime import datetime

import pytest
from django.http import HttpResponse
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView
from pytz import UTC

from django_conditional_views import ConditionalGetDetailViewMixin, ConditionalGetListViewMixin, \
    ConditionalGetMixin, ConditionalGetTemplateViewMixin
from .models import ConditionalGetModel


def get_etag(s):
    etag = hashlib.md5(s.encode('utf8')).hexdigest()
    return f'"{etag}"'


last_modified = datetime(2018, 1, 1, 0, 0, 0, tzinfo=UTC)


@pytest.fixture
def template_name(tmpdir):
    return os.path.join(tmpdir, 'template.html')


@pytest.fixture
def template_on_disk(template_name):
    with open(template_name, 'w') as fp:
        fp.write('Test')
    return template_name


@pytest.fixture(autouse=True)
def test_loader_settings(settings, template_name):
    settings.TEMPLATES = [{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [template_name.rsplit(os.path.sep, maxsplit=1)[0]],
    }]
    return settings


@pytest.fixture
def local_tz():
    return datetime.now().astimezone().tzinfo


@pytest.fixture
def test_request(rf):
    return rf.get('/test')


@pytest.fixture
def base_view():
    class TestView(ConditionalGetMixin, View):
        def get(self, request, *args, **kwargs):
            return HttpResponse()

    return TestView


@pytest.fixture
def template_view(template_on_disk):
    class TestTemplateView(ConditionalGetMixin, TemplateView):
        template_name = 'template.html'

    return TestTemplateView


@pytest.fixture
def conditional_template_view(template_on_disk):
    class TestTemplateView(ConditionalGetTemplateViewMixin, TemplateView):
        template_name = 'template.html'

    return TestTemplateView


@pytest.fixture
def detail_view(template_on_disk):
    class TestDetailView(ConditionalGetMixin, DetailView):
        template_name = 'template.html'
        model = ConditionalGetModel

    return TestDetailView


@pytest.fixture
def conditional_detail_view(template_on_disk):
    class TestDetailView(ConditionalGetDetailViewMixin, DetailView):
        template_name = 'template.html'
        model = ConditionalGetModel

    return TestDetailView


@pytest.fixture
def list_view(template_on_disk):
    class TestListView(ConditionalGetMixin, ListView):
        template_name = 'template.html'
        model = ConditionalGetModel

    return TestListView


@pytest.fixture
def conditional_list_view(template_on_disk):
    class TestListView(ConditionalGetListViewMixin, ListView):
        template_name = 'template.html'
        model = ConditionalGetModel

    return TestListView
