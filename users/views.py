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
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.contrib import messages

from users.forms import UserForm
from radon.model.group import Group
from radon.model.user import User
from radon.model.errors import UserConflictError
from radon.model.payload import (
    PayloadCreateUserRequest,
    PayloadDeleteUserRequest,
    PayloadUpdateUserRequest
)
from radon.model.notification import (
    create_user_request,
    delete_user_request,
    update_user_request,
    wait_response,
)


USERS_HOME = "users:home"

URL_USER_NEW = "users/new.html"

@login_required
def delete_user(request, login):
    """Delete a user"""
    user = User.find(login)
    if not user:
        raise Http404

    if not request.user.administrator:
        raise PermissionDenied
 
    if request.method == "POST":
        payload_json = {
            "obj": {"login": user.login},
            "meta": {"sender": request.user.login}
        }
        
        notif = delete_user_request(PayloadDeleteUserRequest(payload_json))
        resp = wait_response(notif.req_id)

        if resp == 0:
            msg = "User'{}' has been deleted".format(user.login)
        elif resp == 1:
            msg = "Deletion of user '{}' has failed".format(user.login)
        else:
            msg = "Deletion of user '{}' is still pending".format(user.login)
        
        messages.add_message(request, messages.INFO, msg)
        return redirect(USERS_HOME)

    # Requires delete on user
    ctx = {
        "login": login,
    }

    return render(request, "users/delete.html", ctx)


@login_required
def edit_user(request, login):
    """Modify a user"""
    # Requires edit on user
    user = User.find(login)
    if not user:
        raise Http404()
 
    if not request.user.administrator:
        raise PermissionDenied
 
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            obj = {"login": user.login}
            
            if data["email"] != user.email:
                obj["email"] = data["email"]
            if data["administrator"] != user.administrator:
                obj["administrator"] = data["administrator"]
            if data["active"] != user.active:
                obj["active"] = data["active"]
            if data["ldap"] != user.ldap:
                obj["ldap"] = data["ldap"]
            if data["password"] != user.password:
                obj["password"] = data["password"]
            if data["fullname"] != user.fullname:
                obj["fullname"] = data["fullname"]
            
            payload_json = {
                "obj": obj,
                "meta": {"sender": request.user.login}
            }
            
            notif = update_user_request(PayloadUpdateUserRequest(payload_json))
            resp = wait_response(notif.req_id)

            if resp == 0:
                msg = "User '{}' has been updated".format(login)
            elif resp == 1:
                msg = "Modification of user'{}' has failed".format(login)
            else:
                msg = "Modification of user '{}' is still pending".format(login)
                
            messages.add_message(request, messages.INFO, msg)
            return redirect(USERS_HOME)
    else:
        initial_data = {
            "login": user.login,
            "email": user.email,
            "fullname": user.fullname,
            "administrator": user.administrator,
            "active": user.active,
            "ldap": user.ldap,
            "password": user.password,
        }
        form = UserForm(initial=initial_data)

    ctx = {
        "form": form,
        "user": user,
    }
 
    return render(request, "users/edit.html", ctx)


@login_required
def home(request):
    """Homepage for the user view"""
    # TODO: Order by username
    user_objs = list(User.objects.all())
 
    paginator = Paginator(user_objs, 10)
    page_num = request.GET.get("page")
    try:
        page = paginator.page(page_num)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        page = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        page = paginator.page(paginator.num_pages)
    
 
    ctx = {"user": request.user, "page": page, "user_count": len(user_objs)}
    return render(request, "users/home.html", ctx)


@login_required
def new_user(request):
    """Create a new user"""
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            login = data.get("login")
            if User.find(login):
                messages.add_message(
                    request,
                    messages.ERROR,
                    "User '{}' already exists".format(login),
                )
                return render(request, URL_USER_NEW, { 'form': form })
            obj = {
                "login": login,
                "password": data.get("password").encode("ascii", "ignore").decode("utf-8"),
            }
            
            if data.get("email"):
                obj['email'] = data.get("email")
            if data.get("fullname"):
                obj['fullname'] = data.get("fullname")
            obj['administrator'] = data.get("administrator", False)
            obj["active"] = data.get("active", True)
            obj["ldap"] = data.get("ldap", False)
            
            payload_json = {
                "obj": obj,
                "meta": {"sender": request.user.login}
            }
            notif = create_user_request(PayloadCreateUserRequest(payload_json))

            resp = wait_response(notif.req_id)

            if resp == 0:
                msg = "User '{}' has been created".format(login)
            elif resp == 1:
                msg = "Creation of user'{}' has failed".format(login)
            else:
                msg = "Creation of user '{}' is still pending".format(login)
                
            messages.add_message(request, messages.INFO, msg)
            
            return redirect(USERS_HOME)
        else:
            return render(request, URL_USER_NEW, { 'form': form })
    else:
        form = UserForm()
 
    ctx = {
        "form": form,
    }
    return render(request, URL_USER_NEW, ctx)


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
            request.session["user"] = user.login
            return redirect("/")
 
    ctx = {}
    if errors:
        ctx = {"errors": errors}
 
    return render(request, "users/login.html", ctx)


def userlogout(request):
    """Remove a user from the cache -> logout"""
    request.session.flush()
    request.user = None
    return render(request, "users/logout.html", {})


@login_required
def view(request, login):
    """Render the view page for users"""
    # argument is the login name, not the uuid in Cassandra
    user = User.find(login)
    if not user:
        return redirect(USERS_HOME)
 
    ctx = {
        "req_user": request.user,
        "user_obj": user,
        "groups": [Group.find(gname) for gname in user.groups],
    }
    return render(request, "users/view.html", ctx)




