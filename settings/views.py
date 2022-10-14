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

from django import template
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from settings.forms import (
    AddIndexFieldForm
)

from radon.model import Config
from radon import cfg
from radon.database import (
    add_search_field,
    rm_search_field
)


@login_required
def home(request):
    """Default view for Settings"""
    
    indexes = Config.get_search_indexes()    
    
    ctx = {
        "indexes": indexes,
    }
   
    return render(request, "settings/index.html", ctx)


@login_required
def add_index_field(request):
    """Display the form to create a new field"""
    if request.method == "POST":
        form = AddIndexFieldForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            status = add_search_field(data.get("fieldname"), 
                                      data.get("fieldtype"))
            if (status):
                messages.add_message(
                    request,
                    messages.INFO,
                    "The index field '{}' has been created".format(data.get("fieldname")),
                )
            else:
                messages.add_message(
                    request,
                    messages.ERROR,
                    "The index field '{}' has not been created".format(data.get("fieldname")),
                )
                
            return redirect("settings:home")
    else:
        form = AddIndexFieldForm()
        
    ctx = {
        "field_options" : cfg.field_type_interface,
        "form": form,
    }
 
    return render(request, "settings/add_index_field.html", ctx)

@login_required
def rm_index_field(request, field_name):
    """delete_index_field"""
    rm_search_field(field_name)    
    return redirect("settings:home")
    
    
    
    
    
