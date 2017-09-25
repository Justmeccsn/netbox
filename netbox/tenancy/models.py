from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse
from django.utils.encoding import python_2_unicode_compatible

from extras.models import CustomFieldModel, CustomFieldValue
from utilities.models import CreatedUpdatedModel
from utilities.utils import csv_format
from utilities.sql import ObjectFilterQuerySet


class TenantGroupQuerySet(ObjectFilterQuerySet):
    def build_args(self, user):
        return models.Q(tenants__users__in=[user])


@python_2_unicode_compatible
class TenantGroup(models.Model):
    """
    An arbitrary collection of Tenants.
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    objects = TenantGroupQuerySet.as_manager()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return "{}?group={}".format(reverse('tenancy:tenant_list'), self.slug)


class TenantQuerySet(ObjectFilterQuerySet):
    def build_args(self, user):
        return models.Q(users__in=[user])


@python_2_unicode_compatible
class Tenant(CreatedUpdatedModel, CustomFieldModel):
    """
    A Tenant represents an organization served by the NetBox owner. This is typically a customer or an internal
    department.
    """
    name = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(unique=True)
    group = models.ForeignKey('TenantGroup', related_name='tenants', blank=True, null=True, on_delete=models.SET_NULL)
    description = models.CharField(max_length=100, blank=True, help_text="Long-form name (optional)")
    comments = models.TextField(blank=True)
    custom_field_values = GenericRelation(CustomFieldValue, content_type_field='obj_type', object_id_field='obj_id')
    users = models.ManyToManyField(blank=True, related_name='tenants', to=User, verbose_name='Users')

    csv_headers = ['name', 'slug', 'group', 'description']

    objects = TenantQuerySet.as_manager()

    class Meta:
        ordering = ['group', 'name']
        permissions = (
            ('view', 'Can see tenant options'),
        )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tenancy:tenant', args=[self.slug])

    def to_csv(self):
        return csv_format([
            self.name,
            self.slug,
            self.group.name if self.group else None,
            self.description,
        ])
