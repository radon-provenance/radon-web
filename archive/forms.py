# Copyright 2021
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from django import forms
from radon.model import Group

from archive.widgets import JsonPairInputs


def get_groups():
    """Get all the groups defined in the system, adding special groups
    authenticated and anonymous"""
 
    return [(u"AUTHENTICATED@", "authenticated@"), (u"ANONYMOUS@", "anonymous@")] + [
        (g.name, g.name,) for g in Group.objects.all()
    ]
 

class CollectionForm(forms.Form):
    """A form to edit a collection"""
 
    groups = get_groups
 
    metadata = forms.CharField(
        label="Metadata", required=False, widget=JsonPairInputs()
    )
    read_access = forms.MultipleChoiceField(
        required=False, widget=forms.CheckboxSelectMultiple(), choices=groups,
    )
    write_access = forms.MultipleChoiceField(
        required=False, widget=forms.CheckboxSelectMultiple(), choices=groups,
    )
    edit_access = forms.MultipleChoiceField(
        required=False, widget=forms.CheckboxSelectMultiple(), choices=groups,
    )
    delete_access = forms.MultipleChoiceField(
        required=False, widget=forms.CheckboxSelectMultiple(), choices=groups,
    )
 
 
class CollectionNewForm(CollectionForm):
    """A form to create a collection"""
 
    name = forms.CharField(label="Collection name", max_length=100, required=True)
 
 
class ResourceForm(forms.Form):
    """A form to edit a resource"""
 
    groups = get_groups
 
    metadata = forms.CharField(
        label="Metadata", required=False, widget=JsonPairInputs()
    )
    read_access = forms.MultipleChoiceField(
        required=False, widget=forms.CheckboxSelectMultiple(), choices=groups,
    )
    write_access = forms.MultipleChoiceField(
        required=False, widget=forms.CheckboxSelectMultiple(), choices=groups,
    )
    edit_access = forms.MultipleChoiceField(
        required=False, widget=forms.CheckboxSelectMultiple(), choices=groups,
    )
    delete_access = forms.MultipleChoiceField(
        required=False, widget=forms.CheckboxSelectMultiple(), choices=groups,
    )
 
 
class ResourceNewForm(ResourceForm):
    """A form to create a resource"""
 
    name = forms.CharField(label="Item name", max_length=100, required=True)
    file = forms.FileField(required=True)
