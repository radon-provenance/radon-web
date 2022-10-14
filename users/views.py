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
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.contrib import messages

from users.forms import UserForm
from radon.model import (
    Group,
    User
)
from radon.model.errors import UserConflictError


@login_required
def home(request):
    """Homepage for the user view"""
    # TODO: Order by username
    user_objs = list(User.objects.all())
 
    paginator = Paginator(user_objs, 10)
    page = request.GET.get("page")
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        users = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        users = paginator.page(paginator.num_pages)
 
    ctx = {"user": request.user, "users": users, "user_count": len(user_objs)}
    return render(request, "users/index.html", ctx)


def userlogin(request):
    """Try to log a user in the system"""
    if request.method == "GET":
        return render(request, "users/login.html", {})

    errors = ""
    username = request.POST.get("username")
    password = request.POST.get("password")

    invalid = "Username/Password not valid"

    if not username or not password:
        errors = "Username and password are required"

    if not errors:
        user = User.find(username)
        if not user:
            errors = invalid
        else:
            if not user.authenticate(password):
                errors = invalid
 
        if not errors:
            request.session["user"] = user.name
            return redirect("/")
 
    ctx = {}
    if errors:
        ctx = {"errors": errors}
 
    return render(request, "users/login.html", ctx)


@login_required
def delete_user(request, name):
    """Delete a user"""
    user = User.find(name)
    if not user:
        raise Http404

    if not request.user.administrator:
        raise PermissionDenied
 
    if request.method == "POST":
        user.delete(username=request.user.name)
        messages.add_message(
            request, messages.INFO, "User '{}' has been deleted".format(user.name)
        )
        return redirect("users:home")

    # Requires delete on user
    ctx = {
        "user": user,
    }

    return render(request, "users/delete.html", ctx)


@login_required
def edit_user(request, name):
    """Modify a user"""
    # Requires edit on user
    user = User.find(name)
    if not user:
        raise Http404()
 
    if not request.user.administrator:
        raise PermissionDenied
 
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user.update(
                email=data["email"],
                administrator=data["administrator"],
                active=data["active"],
                username=request.user.name,
            )
            if data["password"] != user.password:
                user.update(password=data["password"], username=request.user.name)
            messages.add_message(
                request, messages.INFO, "User '{}' has been updated".format(user.name)
            )
            return redirect("users:home")
    else:
        initial_data = {
            "username": user.name,
            "email": user.email,
            "administrator": user.administrator,
            "active": user.active,
            "password": user.password,
        }
        form = UserForm(initial=initial_data)

    ctx = {
        "form": form,
        "user": user,
    }
 
    return render(request, "users/edit.html", ctx)


@login_required
def new_user(request):
    """Create a new user"""
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            username = data.get("username")
            try:
                user = User.create(
                    name=username,
                    password=data.get("password").encode("ascii", "ignore"),
                    email=data.get("email", ""),
                    administrator=data.get("administrator", False),
                    active=data.get("active", False),
                    username=request.user.name,
                )
                messages.add_message(
                    request,
                    messages.INFO,
                    "User '{}' has been created".format(user.name),
                )
            except UserConflictError:
                messages.add_message(
                    request,
                    messages.ERROR,
                    "User '{}' already exists".format(username),
                )                
            return redirect("users:home")
    else:
        form = UserForm()
 
    ctx = {
        "form": form,
    }
    return render(request, "users/new.html", ctx)


def userlogout(request):
    """Remove a user from the cache -> logout"""
    request.session.flush()
    request.user = None
    return render(request, "users/logout.html", {})


@login_required
def user_view(request, name):
    """Render the view page for users"""
    # argument is the login name, not the uuid in Cassandra
    user = User.find(name)
    if not user:
        return redirect("users:home")
 
    ctx = {
        "req_user": request.user,
        "user_obj": user,
        "groups": [Group.find(gname) for gname in user.groups],
    }
    return render(request, "users/view.html", ctx)
