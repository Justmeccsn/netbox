from __future__ import unicode_literals

from django import forms

from utilities.forms import BootstrapMixin
from utilities.middleware import GlobalUserMiddleware


OBJ_TYPE_CHOICES = [
    ('', 'All Objects'),
    ('Circuits', (
        ('provider', 'Providers'),
        ('circuit', 'Circuits'),
    )),
    ('DCIM', (
        ('site', 'Sites'),
        ('rack', 'Racks'),
        ('devicetype', 'Device types'),
        ('device', 'Devices'),
    )),
    ('IPAM', (
        ('vrf', 'VRFs'),
        ('aggregate', 'Aggregates'),
        ('prefix', 'Prefixes'),
        ('ipaddress', 'IP addresses'),
        ('vlan', 'VLANs'),
    )),
]

OBJ_TYPE_CHOICES_SECRETS = (
    'Secrets', (
        ('secret', 'Secrets'),
    )
)
OBJ_TYPE_CHOICES_TENANCY = (
    'Tenancy', (
        ('tenant', 'Tenants'),
    )
)


class SearchForm(BootstrapMixin, forms.Form):
    q = forms.CharField(
        label='Query', widget=forms.TextInput(attrs={'style': 'width: 350px'})
    )
    obj_type = forms.ChoiceField(
        choices=OBJ_TYPE_CHOICES, required=False, label='Type'
    )

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        user = GlobalUserMiddleware.user()
        if user.has_perm('secrets.view'):
            self.fields['obj_type'].choices += [OBJ_TYPE_CHOICES_SECRETS]
        if user.has_perm('tenancy.view'):
            self.fields['obj_type'].choices += [OBJ_TYPE_CHOICES_TENANCY]
