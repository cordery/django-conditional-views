from datetime import datetime

from django.http import HttpResponse
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView
from pytz import UTC

from django_conditional_views import ConditionalGetDetailViewMixin, \
    ConditionalGetListViewMixin, ConditionalGetMixin, ConditionalGetTemplateViewMixin
from .models import ConditionalGetModel


class SimpleView(ConditionalGetMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponse()


class SimpleEtagView(SimpleView):
    def get_pre_render_etag(self):
        return 'test_etag'


class SimpleLastModifiedView(SimpleView):
    def get_last_modified(self):
        return datetime(2018, 1, 1, 0, 0, 0, tzinfo=UTC)


class SimpleDetailView(ConditionalGetDetailViewMixin, DetailView):
    model = ConditionalGetModel


class AlternativeModifiedDetailView(ConditionalGetDetailViewMixin, DetailView):
    model = ConditionalGetModel
    last_modified_field = 'alternative_modified'


class SimpleListView(ConditionalGetListViewMixin, ListView):
    model = ConditionalGetModel


class AlternativeModifiedListView(ConditionalGetListViewMixin, ListView):
    model = ConditionalGetModel
    last_modified_field = 'alternative_modified'


class PostRenderView(ConditionalGetTemplateViewMixin, TemplateView):
    template_name = 'template.html'
