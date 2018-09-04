import hashlib
import os
from datetime import datetime

import pytest
from pytz import UTC


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
def last_modified():
    return datetime(2018, 1, 1, 0, 0, 0, tzinfo=UTC)


@pytest.fixture
def get_etag():
    def _get_etag(s):
        etag = hashlib.md5(s.encode('utf8')).hexdigest()
        return f'"{etag}"'

    return _get_etag
