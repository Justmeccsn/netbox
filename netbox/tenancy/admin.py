from __future__ import unicode_literals

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.widgets import FilteredSelectMultiple
from .models import TenantGroup


class M2MTenantGroupAdminForm(forms.ModelForm):
    tenants = forms.ModelMultipleChoiceField(
        queryset=TenantGroup.objects.all(),
        required=False,
        widget=FilteredSelectMultiple(
          verbose_name=_('Tenants'),
          is_stacked=False
        )
    )

    def __init__(self, *args, **kwargs):
        super(M2MTenantGroupAdminForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['tenants'].initial = self.instance.tenants.all()

    def save(self, commit=True):
        instance = super(M2MTenantGroupAdminForm, self).save(commit=False)

        if commit:
            instance.save()

        if instance.pk:
            instance.tenants = self.cleaned_data['tenants']
            self.save_m2m()

        return instance


class TenancyUserAdminForm(UserChangeForm, M2MTenantGroupAdminForm):
    pass


class TenancyUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
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

    form = TenancyUserAdminForm


admin.site.unregister(User)
admin.site.register(User, TenancyUserAdmin)
