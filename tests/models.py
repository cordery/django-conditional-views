from django.db import models


class ConditionalGetModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    alternative_modified = models.DateTimeField(blank=True, null=True)
    value = models.CharField(max_length=20, blank=True)
