from __future__ import unicode_literals

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import Group, User
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.widgets import FilteredSelectMultiple
from .models import TenantGroup


class M2MTenantGroupAdminForm(forms.ModelForm):
    tenant_group = forms.ModelMultipleChoiceField(
        queryset=TenantGroup.objects.all(),
        required=False,
        widget=FilteredSelectMultiple(
          verbose_name=_('Tenant Groups'),
          is_stacked=False
        )
    )

    def __init__(self, *args, **kwargs):
        super(M2MTenantGroupAdminForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['tenant_group'].initial = self.instance.tenant_group.all()

    def save(self, commit=True):
        instance = super(M2MTenantGroupAdminForm, self).save(commit=False)

        if commit:
            instance.save()

        if instance.pk:
            instance.tenant_group = self.cleaned_data['tenant_group']
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
                'tenant_group',
                'groups',
                'user_permissions',
            )
        }),
    )

    form = TenancyUserAdminForm


class TenancyGroupAdminForm(M2MTenantGroupAdminForm):
    class Meta:
        model = Group
        fields = '__all__'


class TenancyGroupAdmin(GroupAdmin):
    fieldsets = (
        (None, {'fields': ('name',)}),
        (_('Permissions'), {
            'fields': (
                'tenant_group',
                'permissions',
            )
        }),
    )

    form = TenancyGroupAdminForm


admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(User, TenancyUserAdmin)
admin.site.register(Group, TenancyGroupAdmin)
