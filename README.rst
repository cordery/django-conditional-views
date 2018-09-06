Django Conditional Views
########################

.. image:: https://circleci.com/gh/cordery/django-conditional-views.svg?style=svg
  :target: https://circleci.com/gh/cordery/django-conditional-views
  :alt: Build Status


.. image:: https://codecov.io/gh/cordery/django-conditional-views/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/cordery/django-conditional-views
  :alt: Test Coverage


.. image:: https://readthedocs.org/projects/django-conditional-views/badge/?version=latest
  :target: https://django-conditional-views.readthedocs.io/en/latest/?badge=latest
  :alt: Documentation Status


.. image:: https://img.shields.io/github/license/cordery/django-conditional-views.svg
  :alt: MIT License


Simple ETag and Last-Modified mixins for class based views.


What is Django Conditional Views?
==================================

Django Conditional Views builds off of the built in `django conditional view processing`_ machinery
to provide simple mixins for class based views that implement support for the ETag and Last-Modified
conditional request headers.

.. _django conditional view processing: https://docs.djangoproject.com/en/2.1/topics/conditional-view-processing/


Features
========

Inherit one of these mixins to make your TemplateView's, DetailView's, or ListView's:

  1. Calculate and append ETag and/or Last-Modified headers to the response and;

  2. Respond with a `304 Not Modified`_ or a `412 Precondition Failed`_ to requests that provide conditional response headers such as If-Modified-Since

.. _304 Not Modified: https://tools.ietf.org/html/rfc7232#section-4.1
.. _412 Precondition Failed: https://tools.ietf.org/html/rfc7232#section-4.2

**Helpful Defaults**
  * ETags are automatically generated from the response.content.
  * ETag generation can be customized both before and after the response is rendered.
  * The Last Modified header is automatically set from the last modified timestamp of the template.
  * In the case of the DetailView and ListView mixins, the Last Modified header may also be
    configured to get the last modification timestamp from a field on the model, in which case
    the lastest of that or the template's last modified timestamp will be used.



Getting Started
===============


First install django-conditional-views

.. code-block:: bash

  $ pip install django-conditional-views

Then inherit from one of the following mixins in your views:

* ConditionalGetMixin - Inherits from View
* ConditionalGetTemplateViewMixin - Inherits from TemplateView
* ConditionalGetListViewMixin - Inherits from ListView
* ConditionalGetDetailViewMixin - Inherits from DetailView

See the Usage_ and API_ sections of the documentation_ for more details.

.. _Usage: https://django-conditional-views.readthedocs.io/en/latest/usage.html
.. _API: https://django-conditional-views.readthedocs.io/en/latest/api.html
.. _documentation: https://django-conditional-views.readthedocs.io/en/latest/

Contributing
============

Contributions are welcome.


Getting Started
---------------

To work on the Pendulum codebase, you'll want to clone the project locally
and install the required dependencies via `poetry <https://poetry.eustace.io>`_.

.. code-block:: bash

    $ git clone git@github.com:cordery/django-conditional-views.git
    $ poetry develop


Running Tests
---------------
django-conditional-views uses pytest.  To run tests:

.. code-block:: bash

  $ pytest

