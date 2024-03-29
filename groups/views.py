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
from radon.model import (
    Group,
    User
)
from radon.model.errors import GroupConflictError


@login_required
def add_user(request, name):
    """Add a user to a group"""
    group = Group.find(name)
    if not group:
        raise Http404
    if not request.user.administrator:
        raise PermissionDenied
    users = [(u.name, u.name) for u in User.objects.all() if not group.name in u.groups]
    if request.method == "POST":
        form = GroupAddForm(users, request.POST)
        if form.is_valid():
            data = form.cleaned_data
            new_users = data.get("users", [])
            added, _, _ = group.add_users(new_users, username=request.user.name)
            if added:
                msg = "{} has been added to the group '{}'".format(
                    ", ".join(added), group.name
                )
                group.update(username=request.user.name)
            else:
                msg = "No user has been added to the group '{}'".format(group.name)
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
        group.delete(username=request.user.name)
        messages.add_message(
            request, messages.INFO, "The group '{}' has been deleted".format(group.name)
        )
        return redirect("groups:home")
 
    # Requires delete on user
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
            group.update(name=data["name"], username=request.user.name)
            return redirect("groups:home")
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
        return redirect("groups:home")
        # raise Http404
    ctx = {"user": request.user, "group_obj": group, "members": group.get_usernames()}
    return render(request, "groups/view.html", ctx)
 
 
@login_required
def home(request):
    """"Display the main page fro groups (list of clickable groups)"""
    group_objs = list(Group.objects.all())
 
    paginator = Paginator(group_objs, 10)
    page = request.GET.get("page")
    try:
        groups = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        groups = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        groups = paginator.page(paginator.num_pages)
 
    ctx = {"user": request.user, "groups": groups, "group_count": len(group_objs)}
    return render(request, "groups/index.html", ctx)
 
 
@login_required
def new_group(request):
    """Display the form to create a new group"""
    if request.method == "POST":
        form = GroupForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            groupname = data.get("name")
            try:
                group = Group.create(name=groupname, username=request.user.name)
                messages.add_message(
                    request,
                    messages.INFO,
                    "The group '{}' has been created".format(group.name),
                )
            except GroupConflictError:
                messages.add_message(
                    request,
                    messages.ERROR,
                    "Group '{}' already exists".format(groupname),
                )
            return redirect("groups:home")
    else:
        form = GroupForm()
    ctx = {
        "form": form,
    }
 
    return render(request, "groups/new.html", ctx)
 
 
@login_required
def rm_user(request, name, uname):
    """Remove a user from a group"""
    group = Group.find(name)
    user = User.find(uname)
    if not request.user.administrator:
        raise PermissionDenied
    if user and group:
        removed, not_there, not_exist = group.rm_user(uname, username=request.user.name)
        if removed:
            msg = "'{}' has been removed from the group '{}'".format(uname, name)
        elif not_there:
            msg = "'{}' isn't in the group '{}'".format(uname, name)
        elif not_exist:
            msg = "'{}' doesn't exist".format(uname)
        messages.add_message(request, messages.INFO, msg)
    else:
        raise Http404
    return redirect("groups:view", name=name)
