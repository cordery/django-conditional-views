API
===

Convenience Mixins
++++++++++++++++++

Use one of the following Mixins in your view to enable the conditional request/response features.


.. autoclass:: django_conditional_views.ConditionalGetTemplateViewMixin
   :members: last_modified_elements, post_render_etag_elements
   :undoc-members:

.. autoclass:: django_conditional_views.ConditionalGetDetailViewMixin
   :members: last_modified_elements, post_render_etag_elements
   :undoc-members:


.. autoclass:: django_conditional_views.ConditionalGetListViewMixin
   :members: last_modified_elements, post_render_etag_elements
   :undoc-members:


Base ConditionalGetMixin
++++++++++++++++++++++++

.. autoclass:: django_conditional_views.ConditionalGetMixin
   :members:


Elements
++++++++

Last-Modified Elements
----------------------

.. automodule:: django_conditional_views.elements.etag
   :members:


Etag Elements
-------------

.. automodule:: django_conditional_views.elements.last_modified
   :members:

