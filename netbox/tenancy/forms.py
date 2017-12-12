from __future__ import unicode_literals

from django import forms
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
        fields = ['name', 'slug', 'group', 'description', 'comments', 'users']
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


#
# Tenancy form extension
#

class TenancyForm(ChainedFieldsMixin, FormFilterQuerySets):
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
            self.initial['tenant'] = user.tenants.first()
            self.fields['tenant'].queryset = user.tenants.all()
            self.fields['tenant'].empty_label = None
            self.fields['tenant'].widget = forms.HiddenInput()

            self.fields['tenant_group'].empty_label = None
            self.fields['tenant_group'].widget = forms.HiddenInput()

            try:
                self.initial['tenant_group'] = user.tenants.first().group
            except AttributeError:
                pass
