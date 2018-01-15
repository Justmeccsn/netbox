from __future__ import unicode_literals

from django import forms

from utilities.forms import (
    APISelect, ChainedFieldsMixin, ChainedModelChoiceField, FormFilterQuerySets
)
from utilities.middleware import GlobalUserMiddleware
from .models import Tenant, TenantGroup


#
# Tenancy form extension
#
class TenancyBulkForm(FormFilterQuerySets):
    tenant = forms.ModelChoiceField(queryset=Tenant.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        super(TenancyBulkForm, self).__init__(*args, **kwargs)
        user = GlobalUserMiddleware.user()
        if not user.is_superuser:
            del self.fields['tenant']


class TenancyCSVForm(object):
    def __init__(self, *args, **kwargs):
        super(TenancyCSVForm, self).__init__(*args, **kwargs)
        user = GlobalUserMiddleware.user()
        self.fields['tenant'] = forms.ModelChoiceField(
            queryset=Tenant.objects.all(),
            required=False,
            to_field_name='name',
            help_text='Name of assigned tenant',
            error_messages={
                'invalid_choice': 'Tenant not found.',
            }
        )
        if not user.is_superuser:
            del self.fields['tenant']

    def save(self, *args, **kwargs):
        if 'tenant' not in self.fields:
            self.instance.tenant = GlobalUserMiddleware.user().tenants.first()
            return super(TenancyCSVForm, self).save(*args, **kwargs)
        else:
            return super(TenancyCSVForm, self).save(*args, **kwargs)


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
