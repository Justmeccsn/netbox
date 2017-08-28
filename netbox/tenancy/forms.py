from __future__ import unicode_literals

from django import forms
from django.db.models import Count

from extras.forms import CustomFieldForm, CustomFieldBulkEditForm, CustomFieldFilterForm
from utilities.forms import (
    APISelect, BootstrapMixin, ChainedFieldsMixin, ChainedModelChoiceField, CommentField, FilterChoiceField, SlugField,
)
from utilities.middleware import GlobalUserMiddleware
from .models import Tenant, TenantGroup


#
# Tenant groups
#

class TenantGroupForm(BootstrapMixin, forms.ModelForm):
    slug = SlugField()

    class Meta:
        model = TenantGroup
        fields = ['name', 'slug', 'access_group', 'access_users']


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
        fields = ['name', 'slug', 'group', 'description', 'comments']

    def __init__(self, *args, **kwargs):
        super(TenantForm, self).__init__(*args, **kwargs)
        user = GlobalUserMiddleware.user()
        query = self.fields['group'].queryset
        self.fields['group'].queryset = query.filter_access(user)


class TenantCSVForm(forms.ModelForm):
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

    def __init__(self, *args, **kwargs):
        super(TenantFilterForm, self).__init__(*args, **kwargs)
        query = self.fields['group'].queryset
        self.fields['group'].queryset = query.filter_access(GlobalUserMiddleware.user())


#
# Tenancy form extension
#

class TenancyForm(ChainedFieldsMixin, forms.Form):
    tenant_group = forms.ModelChoiceField(
        queryset=TenantGroup.objects.all(),
        required=False,
        widget=forms.Select(
            attrs={'filter-for': 'tenant', 'nullable': 'true'}
        )
    )
    tenant = ChainedModelChoiceField(
        queryset=Tenant.objects.all(),
        chains=(
            ('group', 'tenant_group'),
        ),
        required=False,
        widget=APISelect(
            api_url='/api/tenancy/tenants/?group_id={{tenant_group}}'
        )
    )

    def __init__(self, *args, **kwargs):

        # Initialize helper selector
        instance = kwargs.get('instance')
        if instance and instance.tenant is not None:
            initial = kwargs.get('initial', {}).copy()
            initial['tenant_group'] = instance.tenant.group
            kwargs['initial'] = initial

        super(TenancyForm, self).__init__(*args, **kwargs)
        user = GlobalUserMiddleware.user()
        if not user.is_superuser:
            query = self.fields['tenant'].queryset
            self.fields['tenant'].queryset = query.filter_access(user)
            self.fields['tenant'].required = True

            query = self.fields['tenant_group'].queryset
            self.fields['tenant_group'].queryset = query.filter_access(user)
            self.fields['tenant_group'].required = True
