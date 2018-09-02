Django Conditional Views
########################

.. image:: https://readthedocs.org/projects/django-conditional-views/badge/?version=latest
  :target: https://django-conditional-views.readthedocs.io/en/latest/?badge=latest
  :alt: Documentation Status

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

Documentation is available at `readthedocs <https://django-conditional-views.readthedocs.io/en/latest/>`_


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

