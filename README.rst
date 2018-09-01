Django Conditional Views
########################

Simple Etag and Last-Modified mixins for class based views.

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

See the documentation for more details.

Documentation
=============

Documentation is available at


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


This is `Python you see`_.

.. _`Python you see`: http://www.python.org/
