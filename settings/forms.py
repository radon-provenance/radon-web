# Copyright 2022
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

from radon import cfg


class AddIndexFieldForm(forms.Form):
    """The collection of fields to add an index field"""
    
    fieldname = forms.CharField(label="fieldname", max_length=100, required=True, initial="new_field")
    
    fieldtype = forms.ChoiceField(widget=forms.Select,
                                  choices=cfg.field_type_interface)
    
    