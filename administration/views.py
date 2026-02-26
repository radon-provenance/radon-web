# Radon Copyright 2025, University of Oxford
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

from django.shortcuts import redirect, render
from django.conf import settings
from django import forms

from radon.model.config import cfg
import radon.database
from radon.model.group import Group
from radon.model.user import User

from project.apps import (
    check_dse,
    check_mqtt
)


class GroupForm(forms.Form):
    grp_name = forms.CharField(label="grp_name", max_length=100)


class UserForm(forms.Form):
    usr_name = forms.CharField(label="usr_name", max_length=100)


def add_group(request):
    if request.method == "POST":
        form = GroupForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            grp_name = data.get('grp_name', '')
            if grp_name:
                radon.database.create_group(grp_name)
        
    return redirect("administration:home")


def add_user(request):
    print("asdd_user")
    if request.method == "POST":
        
        print("asdd_user POST")
        form = UserForm(request.POST)
        if form.is_valid():
            
            print("asdd_user form valid")
            data = form.cleaned_data
            usr_name = data.get('usr_name', '')
            print(usr_name)
            if usr_name:
                radon.database.create_user(usr_name, "radon")
        
    return redirect("administration:home")

def rm_group(request, grp_name):
    if grp_name:
        radon.database.delete_group(grp_name)
    return redirect("administration:home")

def rm_user(request, usr_name):
    if usr_name:
        radon.database.delete_user(usr_name)
    return redirect("administration:home")


def create_keyspace(request):
    radon.database.create_keyspace()
    return redirect("administration:home")


def create_default_groups(request):
    radon.database.create_default_groups()
    return redirect("administration:home")


def create_default_users(request):
    radon.database.create_default_users()
    return redirect("administration:home")


def home(request):
    """Default view for Settings"""
    if settings.DSE_CONNECT and settings.DSE_KEYSPACE and settings.DSE_POPULATED:
        return redirect("home")
    
    check_dse()
    check_mqtt()
    
    group_objs = []
    groups_names = []
    if settings.DSE_CONNECT and settings.DSE_KEYSPACE:
        group_objs = list(Group.objects.all())
        groups_names = [ el.name for el in group_objs ]
        groups_names.sort()
    
    user_objs = []
    users_names = []
    if settings.DSE_CONNECT and settings.DSE_KEYSPACE:
        user_objs = list(User.objects.all())
        users_names = [ el.login for el in user_objs ]
        users_names.sort()
    
    ctx = {
        "ks_name": cfg.dse_keyspace,
        "ks_ok": settings.DSE_KEYSPACE,
        "groups": groups_names,
        "users": users_names
    }
    
    return render(request, "administration/index.html", ctx)