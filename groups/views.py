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

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404
from django.contrib import messages
from django.core.exceptions import PermissionDenied
 
from groups.forms import (
    GroupForm,
    GroupAddForm
)
from radon.model.group import Group
from radon.model.notification import (
    create_group_request,
    delete_group_request,
    update_group_request,
    wait_response,
)
from radon.model.payload import (
    PayloadCreateGroupRequest,
    PayloadDeleteGroupRequest,
    PayloadUpdateGroupRequest,
)
from radon.model.user import User


GROUP_HOME = "groups:home"
URL_GROUP_NEW = "groups/new.html"


@login_required
def add_user(request, name):
    """Add a user to a group"""
    group = Group.find(name)
    if not group:
        raise Http404
    if not request.user.administrator:
        raise PermissionDenied
    users = [(u.login, group.name in u.groups) for u in User.objects.all()]
    if request.method == "POST":
        form = GroupAddForm(users, request.POST)
        if form.is_valid():
            data = form.cleaned_data

            payload_json = {
                "obj": {
                    "name": name,
                    "members": data.get("users", [])
                }, 
                "meta": {"sender": request.user.login}
            }

            notif = update_group_request(PayloadUpdateGroupRequest(payload_json))
            resp = wait_response(notif.req_id)

            if resp == 0:
                msg = "Group '{}' has been updated".format(group.name)
            elif resp == 1:
                msg = "Modification of group'{}' has failed".format(group.name)
            else:
                msg = "Modification of group '{}' is still pending".format(group.name)
                
            messages.add_message(request, messages.INFO, msg)
            
            return redirect("groups:view", name=name)
 
    else:
        form = GroupAddForm(users)
 
    ctx = {"group": group, "form": form, "users": users}
    return render(request, "groups/add.html", ctx)
 
 
@login_required
def delete_group(request, name):
    """Delete a group"""
    group = Group.find(name)
    if not group:
        raise Http404
    if not request.user.administrator:
        raise PermissionDenied
    if request.method == "POST":
        payload_json = {
            "obj": {"name": group.name},
            "meta": {"sender": request.user.login}
        }
        
        notif = delete_group_request(PayloadDeleteGroupRequest(payload_json))

        resp = wait_response(notif.req_id)

        if resp == 0:
            msg = "Group '{}' has been deleted".format(group.name)
        elif resp == 1:
            msg = "Deletion of group '{}' has failed".format(group.name)
        else:
            msg = "Deletion of group '{}' is still pending".format(group.name)
        
        messages.add_message(request, messages.INFO, msg)
        
        return redirect(GROUP_HOME)

    ctx = {
        "group": group,
    }
    return render(request, "groups/delete.html", ctx)
 
 
@login_required
def edit_group(request, name):
    """Edit a group (add/delete users)"""
    group = Group.find(name)
    if not group:
        raise Http404()
 
    if not request.user.administrator:
        raise PermissionDenied
 
    if request.method == "POST":
        form = GroupForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            payload_json = {
                "obj": {
                    "name": group.name,
                    "members": data.get("users", [])
                },
                "meta": {
                    "sender": request.user.login
                }
            }
            notif = update_group_request(PayloadUpdateGroupRequest(payload_json))
            resp = wait_response(notif.req_id)

            if resp == 0:
                msg = "Group '{}' has been updated".format(group.name)
            elif resp == 1:
                msg = "Modification of group'{}' has failed".format(group.name)
            else:
                msg = "Modification of group '{}' is still pending".format(group.name)
                
            messages.add_message(request, messages.INFO, msg)
            
            return redirect(GROUP_HOME)
    else:
        initial_data = {"name": group.name}
        form = GroupForm(initial=initial_data)
 
    ctx = {
        "form": form,
        "group": group,
    }
 
    return render(request, "groups/edit.html", ctx)


@login_required
def group_view(request, name):
    """Display the content of a group (users)"""
    group = Group.find(name)
    if not group:
        return redirect(GROUP_HOME)
    ctx = {"user": request.user, "group": group, "members": group.get_members()}
    return render(request, "groups/view.html", ctx)


@login_required
def home(request):
    """"Display the main page fro groups (list of clickable groups)"""
    group_objs = list(Group.objects.all())
 
    paginator = Paginator(group_objs, 10)
    page_num = request.GET.get("page")
    try:
        page = paginator.page(page_num)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        page = paginator.page(paginator.num_pages)
 
    ctx = {"user": request.user, "page": page, "group_count": len(group_objs)}
    return render(request, "groups/home.html", ctx)
 
 
@login_required
def new_group(request):
    """Display the form to create a new group"""
    if request.method == "POST":
        form = GroupForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            groupname = data.get("name")
            if Group.find(groupname):
                messages.add_message(
                    request,
                    messages.ERROR,
                    "Group '{}' already exists".format(groupname),
                )
                return render(request, URL_GROUP_NEW, { 'form': form })
            
            payload_json = {
                "obj": {"name": groupname,},
                "meta": {"sender": request.user.login}
            }
            notif = create_group_request(PayloadCreateGroupRequest(payload_json))

            resp = wait_response(notif.req_id)

            if resp == 0:
                msg = "Group '{}' has been created".format(groupname)
            elif resp == 1:
                msg = "Creation of group'{}' has failed".format(groupname)
            else:
                msg = "Creation of group '{}' is still pending".format(groupname)
                
            messages.add_message(request, messages.INFO, msg)
            return redirect(GROUP_HOME)
        else:
            return render(request, URL_GROUP_NEW, { 'form': form })
    else:
        form = GroupForm()
    
    ctx = {
        "form": form,
    }
    return render(request, URL_GROUP_NEW, ctx)
 
 
@login_required
def rm_user(request, name, uname):
    """Remove a user from a group"""
    group = Group.find(name)
    user = User.find(uname)
    if not request.user.administrator:
        raise PermissionDenied
    if user and group:
        lm = group.get_members()
        lm.remove(uname)
        
        payload_json = {
            "obj": {
                "name": name,
                "members": lm
            }, 
            "meta": {"sender": request.user.login}
        }
        
        notif = update_group_request(PayloadUpdateGroupRequest(payload_json))
        resp = wait_response(notif.req_id)

        if resp == 0:
            msg = "Group '{}' has been updated".format(group.name)
        elif resp == 1:
            msg = "Modification of group'{}' has failed".format(group.name)
        else:
            msg = "Modification of group '{}' is still pending".format(group.name)
                
            messages.add_message(request, messages.INFO, msg)
            
    else:
        raise Http404
    return redirect("groups:view", name=name)
