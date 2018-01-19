from __future__ import unicode_literals

from django import forms
from django.contrib.auth.models import User
from django.db.models import Count

from extras.forms import CustomFieldForm, CustomFieldBulkEditForm, CustomFieldFilterForm
from utilities.forms import (
    APISelect, BootstrapMixin, ChainedFieldsMixin, ChainedModelChoiceField, CommentField, FilterChoiceField, SlugField,
    FormFilterQuerySets, ModelFormFilterQuerySets
)
from utilities.middleware import GlobalUserMiddleware
from .models import Tenant, TenantGroup

#
# Tenant groups
#

class TenantGroupForm(BootstrapMixin, ModelFormFilterQuerySets):
    slug = SlugField()

    class Meta:
        model = TenantGroup
        fields = ['name', 'slug']


#
# Tenants
#

class TenantForm(BootstrapMixin, CustomFieldForm):
    slug = SlugField()
    comments = CommentField()
    group = forms.ModelChoiceField(
        queryset=TenantGroup.objects.all(),
        required=False,
    )

    class Meta:
        model = Tenant
        fields = ['name', 'slug', 'group', 'description', 'comments', 'users']

    def __init__(self, *args, **kwargs):
        super(TenantForm, self).__init__(*args, **kwargs)
        user = GlobalUserMiddleware.user()
        query = self.fields['group'].queryset
        self.fields['group'].queryset = query.filter_access(user)


class TenantCSVForm(ModelFormFilterQuerySets):
    slug = SlugField()
    group = forms.ModelChoiceField(
        queryset=TenantGroup.objects.all(),
        required=False,
        to_field_name='name',
        help_text='Name of parent group',
        error_messages={
            'invalid_choice': 'Group not found.'
        }
    )

    class Meta:
        model = Tenant
        fields = ['name', 'slug', 'group', 'description', 'comments']
        help_texts = {
            'name': 'Tenant name',
            'comments': 'Free-form comments'
        }


class TenantBulkEditForm(BootstrapMixin, CustomFieldBulkEditForm):
    pk = forms.ModelMultipleChoiceField(queryset=Tenant.objects.all(), widget=forms.MultipleHiddenInput)
    group = forms.ModelChoiceField(queryset=TenantGroup.objects.all(), required=False)

    class Meta:
        nullable_fields = ['group']


class TenantFilterForm(BootstrapMixin, CustomFieldFilterForm):
    model = Tenant
    q = forms.CharField(required=False, label='Search')
    group = FilterChoiceField(
        queryset=TenantGroup.objects.annotate(filter_count=Count('tenants')),
        to_field_name='slug',
        null_option=(0, 'None')
    )
