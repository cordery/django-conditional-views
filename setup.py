# -*- coding: utf-8 -*-
from distutils.core import setup

package_dir = \
    {'': 'src'}

packages = \
    ['django_conditional_views']

package_data = \
    {'': ['*']}

install_requires = \
    ['django>=2.1,<3.0']

setup_kwargs = {
    'name': 'django-conditional-views',
    'version': '0.1.0',
    'description': 'Simple Etag and Last-Modified mixins for class based views.',
    'long_description': None,
    'author': 'Andrew Cordery',
    'author_email': 'cordery@gmail.com',
    'url': None,
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.6,<4.0',
}

setup(**setup_kwargs)
