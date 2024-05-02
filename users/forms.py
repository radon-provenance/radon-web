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

 
class UserForm(forms.Form):
    """Fields for the user form"""
 
    login = forms.CharField(label="login", max_length=100, required=True)
    password = forms.CharField(widget=forms.PasswordInput(), required=True)
    fullname = forms.CharField(label="Fullname", max_length=100, required=False)
    email = forms.CharField(label="Email", max_length=100, required=False)
    active = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    administrator = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    ldap = forms.BooleanField(widget=forms.CheckboxInput, required=False)
