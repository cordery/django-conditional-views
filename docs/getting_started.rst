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

See the :doc:`api` documentation for more details.

