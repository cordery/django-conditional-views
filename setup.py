# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = {'': 'src'}

packages = ['django_conditional_views']

package_data = {'': ['*']}

install_requires = ['django>=2.1,<3.0']

long_description = open("README.rst", "r").read()

setup_kwargs = {
    'name': 'django-conditional-views',
    'version': '0.1.1',
    'description': 'Simple Etag and Last-Modified mixins for class based views.',
    'long_description': long_description,
    'author': 'Andrew Cordery',
    'author_email': 'cordery@gmail.com',
    'url': 'https://github.com/cordery/django-conditional-views',
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.6,<4.0',
    'classifiers': [
        "Framework :: Django",
        "Framework :: Django :: 2.1",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
}

setup(**setup_kwargs)
