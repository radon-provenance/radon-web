# Radon Copyright 2021, University of Oxford
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
 
 
class GroupForm(forms.Form):
    """The collection of fields to display a group"""
    name = forms.CharField(label="Username", max_length=100, required=True)
 
 
class GroupAddForm(forms.Form):
    """The collection of fields to add a group"""
    def __init__(self, users, *args, **kwargs):
        super(GroupAddForm, self).__init__(*args, **kwargs)
        self.fields["users"] = forms.MultipleChoiceField(
            widget=forms.CheckboxSelectMultiple, choices=users
        )
