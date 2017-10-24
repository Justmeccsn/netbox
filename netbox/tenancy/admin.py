from __future__ import unicode_literals

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import (
    UserCreationForm,
    UserChangeForm,
)
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.widgets import AdminRadioSelect
from .models import Tenant


class M2MTenantGroupAdminForm(forms.ModelForm):
    tenants = forms.ModelChoiceField(
        queryset=Tenant.objects.all(),
        required=True,
        widget=AdminRadioSelect(),
        empty_label=None,
    )

    def __init__(self, *args, **kwargs):
        super(M2MTenantGroupAdminForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            try:
                self.fields['tenants'].initial = self.instance.tenants.all()[0]
            except:
                pass

    def save(self, commit=True):
        instance = super(M2MTenantGroupAdminForm, self).save(commit=False)

        if commit:
            instance.save()

        if instance.pk:
            instance.tenants.add(self.cleaned_data['tenants'])

        return instance


class TenancyUserAdminForm(UserChangeForm, M2MTenantGroupAdminForm):
    pass


class TenancyUserCreationForm(UserCreationForm, M2MTenantGroupAdminForm):

    def save(self, commit=True):
        instance = super(TenancyUserCreationForm, self).save(commit=commit)
        if not instance.pk:
            instance.save()
            instance.tenants.add(self.cleaned_data['tenants'])
        return instance


class TenancyUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_active', 'is_superuser', 'user_tenant', 'user_group')

    fieldsets = (
        (None, {
            'fields': (
                'username',
                'email',
                'password',
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_superuser',
                'tenants',
                'groups',
                'user_permissions',
            )
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email'),
        }),
        (_('Permissions'), {
            'fields': (
                'is_superuser',
                'tenants',
                'groups',
                'user_permissions',
            )
        }),
    )

    add_form = TenancyUserCreationForm
    form = TenancyUserAdminForm

    def user_tenant(self, obj):
        try:
            return format_html(
                '<a href="{}">{}</a>',
                '{}/change'.format(obj.id),
                obj.tenants.all()[0],
            )
        except:
            return 'None'
    user_tenant.short_description = 'Tenant'

    def user_group(self, obj):
        try:
            group = obj.groups.all()[0]
            return format_html(
                '<a href="{}">{}</a>',
                '/admin/auth/group/{}/change'.format(group.id),
                group,
            )
        except:
            return 'None'
    user_group.short_description = 'Permissions Group'


admin.site.unregister(User)
admin.site.register(User, TenancyUserAdmin)
