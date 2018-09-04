Usage
=====

Adding a ConditionalGet mixin will make your class based views:

  A) Calculate and append Etag and/or Last-Modified headers to each response and;

  B) Return a 304 (Not Modified) or 412 (Precondition Failed) response if applicable.


In most cases, the predefined convenience mixins will be suitable for your views.
Simply add the appropriate mixin to your view class to enable the functionality.

TemplateViews
+++++++++++++

The ``ConditionalGetTemplateViewMixin`` is appropriate for TemplateViews.

For example:

.. code-block:: python

  class MyView(ConditionalGetTemplateViewMixin, TemplateView):
    template_name = 'my_template.html'


.. autoclass:: django_conditional_views.ConditionalGetTemplateViewMixin
   :members: last_modified_elements, post_render_etag_elements
   :undoc-members:
   :noindex:


Model Views
++++++++++++

The ``ConditionalGetDetailViewMixin`` is appropriate for DetailViews.

You may set the ``last_modified_field`` property on the view to control which field on the model
contains the last modified timestamp.  This field defaults to 'modified'.

For example:

.. code-block:: python

  class MyModel(models.Model):
    name = models.CharField(max_length=255)
    modified = models.DateTimeField(auto_now=True)

  class MyView(ConditionalGetDetailViewMixin, DetailView):
    model = MyModel

  class MyOtherModel(models.Model):
    name = models.CharField(max_length=255)
    last_modified = models.DateTimeField(auto_now=True)

  class MyOtherView(ConditionalGetDetailViewMixin, DetailView):
    model = MyModel
    last_modified_field = 'last_modified'


.. autoclass:: django_conditional_views.ConditionalGetDetailViewMixin
   :members: last_modified_elements, post_render_etag_elements
   :undoc-members:
   :noindex:



The ``ConditionalGetListViewMixin`` is appropriate for ListViews.

You may set the ``last_modified_field`` property on the view to control which field on the model
contains the last modified timestamp.  This field defaults to 'modified'.  The most recent value
for this field in the queryset will be used.

For example:

.. code-block:: python

  class MyModel(models.Model):
    name = models.CharField(max_length=255)
    modified = models.DateTimeField(auto_now=True)

  class MyView(ConditionalGetListViewMixin, ListView):
    model = MyModel

  class MyOtherModel(models.Model):
    name = models.CharField(max_length=255)
    last_modified = models.DateTimeField(auto_now=True)

  class MyOtherView(ConditionalGetListViewMixin, ListView):
    model = MyModel
    last_modified_field = 'last_modified'


.. autoclass:: django_conditional_views.ConditionalGetListViewMixin
   :members: last_modified_elements, post_render_etag_elements
   :undoc-members:
   :noindex:


Customizing Etag & Last-Modified Generation
+++++++++++++++++++++++++++++++++++++++++++

The convenience mixins and the underlying ``ConditionalGetViewMixin`` compute the Etag and
Last-Modified headers by calling a method which iterates through a list of *elements* stored in
a property of the view class.  See the individual header sections below for details.

Elements can be either a function or a class with a ``__call__`` method (several useful base classes are
provided in the ``django_conditional_views.elements module``).  Elements take the view instance as the
only argument and return either ``None``, a ``str`` (ETag) or a ``datetime.datetime`` (Last Modified).

To customize how either header is generated you may override the elements properties,
define your own elements, or override the get methods entirely.  See the :doc:`api` docs for details on
the classes.



Last-Modified
-------------
The last-modified timestamp is calculated before the response is rendered by a call to the
``get_last_modified`` method, which by default takes the latest datetime returned by each
function/object in the ``last_modified_elements`` view property.


Etag
----

Etags can be calculated both before and after the response is rendered.  The benefit of calculating
an etag before the response is rendered is that if the etag provided by the request matches the
calculated etag, then the effort to render the response can be skipped.

Pre-render etags are computed by a call to the ``get_pre_rendered_etag`` method of the view, which by
default calculates an etag by concatenating the output of each function/object in the
``pre_render_etag_elements`` view property.

Post-render etags are computed by a call to the ``get_post_rendered_etag`` method of the view, which by
default calculates an etag by concatenating the output of each function/object in the
``post_render_etag_elements`` view property.


