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


import json
from django.utils.translation import ugettext_lazy as _
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_206_PARTIAL_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_409_CONFLICT,
)

from project.custom import CassandraAuthentication

from radon.model import Group
from radon.model import User


MSG_LACK_AUTHORIZATION = "User lack authorization"
MSG_METH_NOT_ALLOWED = "Method Not Allowed"
MSG_INVALID_JSON = "Invalid JSON body"


@api_view(["GET"])
@authentication_classes((CassandraAuthentication,))
@permission_classes((IsAuthenticated,))
def authenticate(request):
    """Authenticate a user"""
    msg = u"User {} is authenticated".format(request.user.login)
    return Response({"message": msg})


@api_view(["GET", "DELETE", "PUT"])
@authentication_classes((CassandraAuthentication,))
@permission_classes((IsAuthenticated,))
def group(request, groupname):
    """REST calls to manage a group"""
    if request.method == "GET":
        return ls_group(groupname)
    elif request.method == "DELETE":
        if request.user and request.user.administrator:
            return delete_group(groupname)
        else:
            return Response(MSG_LACK_AUTHORIZATION, status=HTTP_403_FORBIDDEN)
    elif request.method == "PUT":
        if request.user and request.user.administrator:
            return modify_group(request, groupname)
        else:
            return Response(MSG_LACK_AUTHORIZATION, status=HTTP_403_FORBIDDEN)
    else:
        return Response(MSG_METH_NOT_ALLOWED, status=HTTP_405_METHOD_NOT_ALLOWED)


@api_view(["GET", "POST"])
@authentication_classes((CassandraAuthentication,))
@permission_classes((IsAuthenticated,))
def groups(request):
    """REST calls to manage groups"""
    if request.method == "GET":
        return Response([u.name for u in Group.objects.all()])
    elif request.method == "POST":
        if request.user and request.user.administrator:
            return create_group(request)
        else:
            return Response(MSG_LACK_AUTHORIZATION, status=HTTP_403_FORBIDDEN)
    else:
        return Response(MSG_METH_NOT_ALLOWED, status=HTTP_405_METHOD_NOT_ALLOWED)


@api_view(["GET", "PUT", "DELETE"])
@authentication_classes((CassandraAuthentication,))
@permission_classes((IsAuthenticated,))
def user(request, username):
    """REST calls to manage a user"""
    if request.method == "GET":
        return ls_user(username)
    elif request.method == "PUT":
        if request.user and request.user.administrator:
            return modify_user(request, username)
        else:
            return Response(MSG_LACK_AUTHORIZATION, status=HTTP_403_FORBIDDEN)
    elif request.method == "DELETE":
        if request.user and request.user.administrator:
            return delete_user(username)
        else:
            return Response(MSG_LACK_AUTHORIZATION, status=HTTP_403_FORBIDDEN)
    else:
        return Response(MSG_METH_NOT_ALLOWED, status=HTTP_405_METHOD_NOT_ALLOWED)


def create_group(request):
    """Expecting json in the body:
    { "groupname": groupname }
    """
    try:
        body = request.body
        request_body = json.loads(body)
    except (TypeError, json.JSONDecodeError):
        return Response(MSG_INVALID_JSON, status=HTTP_400_BAD_REQUEST)
    try:
        groupname = request_body["groupname"]
    except KeyError:
        return Response("Missing groupname", status=HTTP_400_BAD_REQUEST)
    group_db = Group.find(groupname)
    if group_db:
        return Response("Group already exists", status=HTTP_409_CONFLICT)
    new_group_db = Group.create(name=groupname)
    return Response(new_group_db.to_dict(), status=HTTP_201_CREATED)


def create_user(request):
    """Expecting json in the body:
    { "username": username,
      "password": password,
      "email": email,
      "administrator": is_admin }
    """
    try:
        body = request.body
        request_body = json.loads(body)
    except (TypeError, json.JSONDecodeError):
        return Response(MSG_INVALID_JSON, status=HTTP_400_BAD_REQUEST)
    try:
        username = request_body["username"]
    except KeyError:
        return Response("Missing username", status=HTTP_400_BAD_REQUEST)
    user_db = User.find(username)
    if user_db:
        return Response("User already exists", status=HTTP_409_CONFLICT)
    try:
        email = request_body["email"]
    except KeyError:
        return Response("Missing email", status=HTTP_400_BAD_REQUEST)
    try:
        password = request_body["password"]
    except KeyError:
        return Response("Missing password", status=HTTP_400_BAD_REQUEST)
    administrator = request_body.get("administrator", False)
    new_user_db = User.create(
        name=username, password=password, email=email, administrator=administrator
    )
    return Response(new_user_db.to_dict(), status=HTTP_201_CREATED)


def delete_group(groupname):
    """Delete a group"""
    group_db = Group.find(groupname)
    if not group_db:
        return Response(
            u"Group {} doesn't exist".format(groupname), status=HTTP_404_NOT_FOUND
        )
    group_db.delete()
    return Response(u"Group {} has been deleted".format(groupname), status=HTTP_200_OK)


def delete_user(username):
    """Delete a user"""
    user_db = User.find(username)
    if not user_db:
        return Response(
            u"User {} doesn't exist".format(username), status=HTTP_404_NOT_FOUND
        )
    user_db.delete()
    return Response(u"User {} has been deleted".format(username), status=HTTP_200_OK)


def add_user_group(group_db, ls_users):
    """Add a user (or a list of users) to a group"""
    # Check that all users exists
    added, not_added, already_there = group_db.add_users(ls_users)
    msg = []

    if added:
        msg.append(u"Added {} to the group {}".format(", ".join(added), group_db.name))
    if already_there:
        if len(already_there) == 1:
            verb = "is"
        else:
            verb = "are"
        msg.append(
            u"{} {} already in the group {}".format(
                ", ".join(already_there), verb, group_db.name
            )
        )
    if not_added:
        msg.append(u"{} doesn't exist".format(", ".join(not_added)))
    msg = ", ".join(msg)
    if not_added or already_there:
        return Response(msg, status=HTTP_206_PARTIAL_CONTENT)
    else:
        return Response(msg, status=HTTP_200_OK)


def rm_user_group(group_db, ls_users):
    """Remove a user (or a list of users) from a group"""
    removed, not_there, not_exist = group_db.rm_users(ls_users)
    msg = []

    if removed:
        msg.append(
            u"Removed {} from the group {}".format(", ".join(removed), group_db.name)
        )
    if not_there:
        if len(not_there) == 1:
            verb = "isn't"
        else:
            verb = "aren't"
        msg.append(
            u"{} {} in the group {}".format(", ".join(not_there), verb, group_db.name)
        )
    if not_exist:
        msg.append(u"{} doesn't exist".format(", ".join(not_exist)))
    msg = ", ".join(msg)
    if not_there or not_exist:
        return Response(msg, status=HTTP_206_PARTIAL_CONTENT)
    else:
        return Response(msg, status=HTTP_200_OK)


def modify_group(request, groupname):
    """Expecting json in the body:
    {
      "add_users": [user1, user2, ...],
      "rm_users": [user1, user2, ...]
    }
    """
    try:
        body = request.body
        request_body = json.loads(body)
    except (TypeError, json.JSONDecodeError):
        return Response(MSG_INVALID_JSON, status=HTTP_400_BAD_REQUEST)
    group_db = Group.find(groupname)
    if not group_db:
        return Response(
            u"Group {} doesn't exist".format(groupname), status=HTTP_404_NOT_FOUND
        )

    # Add users to group
    if "add_users" in request_body:
        return add_user_group(group_db, request_body["add_users"])
    # Remove users from group
    if "rm_users" in request_body:
        return rm_user_group(group_db, request_body["rm_users"])

    return Response("Bad request", status=HTTP_400_BAD_REQUEST)


def ls_group(groupname):
    """Get a list of groups"""
    group_db = Group.find(groupname)
    try:
        return Response(group_db.to_dict())
    except NameError:
        return Response(
            u"Group {} not found".format(groupname), status=HTTP_404_NOT_FOUND
        )


def modify_user(request, username=""):
    """Expecting json in the body:
    { "username": username,
      "password": password,
      "email": email,
      "administrator": is_admin,
      "active": is_active}
    """
    try:
        body = request.body
        request_body = json.loads(body)
    except (TypeError, json.JSONDecodeError):
        return Response(MSG_INVALID_JSON, status=HTTP_400_BAD_REQUEST)
    if username is None:
        try:
            username = request_body["username"]
        except KeyError:
            return Response("Missing username", status=HTTP_400_BAD_REQUEST)
    user_db = User.find(username)
    if not user_db:
        return Response(
            u"User {} doesn't exist".format(username), status=HTTP_404_NOT_FOUND
        )
    if "email" in request_body:
        user_db.update(email=request_body["email"])
    if "password" in request_body:
        user_db.update(password=request_body["password"])
    if "administrator" in request_body:
        user_db.update(administrator=request_body["administrator"])
    if "active" in request_body:
        user_db.update(active=request_body["active"])
    return Response(user_db.to_dict(), status=HTTP_200_OK)


def ls_user(username):
    """List user info"""
    user_db = User.find(username)
    if user_db:
        return Response(user_db.to_dict(), status=HTTP_200_OK)
    else:
        return Response(
            u"User {} not found".format(username), status=HTTP_404_NOT_FOUND
        )


@api_view(["GET", "POST"])
@authentication_classes((CassandraAuthentication,))
@permission_classes((IsAuthenticated,))
def users(request):
    """REST calls for users"""
    if request.method == "GET":
        return Response([u.login for u in User.objects.all()])
    elif request.method == "POST":
        return create_user(request)
    else:
        return Response(MSG_METH_NOT_ALLOWED, status=HTTP_405_METHOD_NOT_ALLOWED)
