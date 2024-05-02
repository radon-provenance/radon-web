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
    HTTP_202_ACCEPTED,
    HTTP_206_PARTIAL_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_409_CONFLICT,
)

from project.custom import CassandraAuthentication

from radon.model.group import Group
from radon.model.user import User
from radon.model.notification import (
    create_group_request,
    delete_group_request,
    update_group_request,
    create_user_request,
    delete_user_request,
    update_user_request,
    wait_response,
)
from radon.model.payload import (
    PayloadCreateGroupRequest,
    PayloadDeleteGroupRequest,
    PayloadUpdateGroupRequest,
    PayloadCreateUserRequest,
    PayloadDeleteUserRequest,
    PayloadUpdateUserRequest,
)



MSG_LACK_AUTHORIZATION = "User lack authorization"
MSG_METH_NOT_ALLOWED = "Method Not Allowed"
MSG_INVALID_JSON = "Invalid JSON body"


def add_user_group(request, group_db, ls_users):
    """Add a user (or a list of users) to a group"""
    new_members = list(set(group_db.get_members()) | set(ls_users))
    payload_json = {
        "obj": {
            "name": group_db.name,
            "members": new_members
        }, 
        "meta": {"sender": request.user.login}
    }

    notif = update_group_request(PayloadUpdateGroupRequest(payload_json))
    resp = wait_response(notif.req_id)

    if resp == 0:
        return Response(group_db.to_dict(), status=HTTP_200_OK)
    elif resp == 1:
        return Response("Modification of group'{}' has failed".format(group_db.name),
                        status=HTTP_400_BAD_REQUEST)
    else:
        return Response("Modification of group'{}' is still pending".format(group_db.name),
                        status=HTTP_202_ACCEPTED)


@api_view(["GET"])
@authentication_classes((CassandraAuthentication,))
@permission_classes((IsAuthenticated,))
def authenticate(request):
    """Authenticate a user"""
    msg = u"User {} is authenticated".format(request.user.login)
    return Response({"message": msg})


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
    
    payload_json = {
        "obj": {"name": groupname,},
        "meta": {"sender": request.user.login}
    }
    notif = create_group_request(PayloadCreateGroupRequest(payload_json))

    resp = wait_response(notif.req_id)

    if resp == 0:
        new_group_db = Group.find(groupname)
        return Response(new_group_db.to_dict(), status=HTTP_201_CREATED)
    elif resp == 1:
        return Response("Creation of group'{}' has failed".format(groupname),
                        status=HTTP_400_BAD_REQUEST)
    else:
        return Response("Creation of group'{}' is still pending".format(groupname),
                        status=HTTP_202_ACCEPTED)


def create_user(request):
    """Expecting json in the body:
    { "login": login,
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
        login = request_body["login"]
    except KeyError:
        return Response("Missing login", status=HTTP_400_BAD_REQUEST)
    user_db = User.find(login)
    if user_db:
        return Response("User already exists", status=HTTP_409_CONFLICT)
    
    try:
        password = request_body["password"]
    except KeyError:
        return Response("Missing password", status=HTTP_400_BAD_REQUEST)

    obj = {
        "login": login,
        "password": password
    }
    
    if "email" in request_body:
        obj['email'] = request_body.get("email")
    if "fullname" in request_body:
        obj['fullname'] = request_body.get("fullname")
    obj['administrator'] = request_body.get("administrator", False)
    obj["active"] = request_body.get("active", True)
    obj["ldap"] = request_body.get("ldap", False)
            
    payload_json = {
        "obj": obj,
        "meta": {"sender": request.user.login}
    }
    
    notif = create_user_request(PayloadCreateUserRequest(payload_json))
    resp = wait_response(notif.req_id)

    if resp == 0:
        new_user_db = User.find(login)
        return Response(new_user_db.to_dict(), status=HTTP_201_CREATED)
    elif resp == 1:
        return Response("Creation of user'{}' has failed".format(login),
                        status=HTTP_400_BAD_REQUEST)
    else:
        return Response("Creation of user'{}' is still pending".format(login),
                        status=HTTP_202_ACCEPTED)


def delete_group(request, groupname):
    """Delete a group"""
    group_db = Group.find(groupname)
    if not group_db:
        return Response(
            u"Group {} doesn't exist".format(groupname), status=HTTP_404_NOT_FOUND
        )

    payload_json = {
        "obj": {"name": groupname},
        "meta": {"sender": request.user.login}
    }

    notif = delete_group_request(PayloadDeleteGroupRequest(payload_json))
    resp = wait_response(notif.req_id)

    if resp == 0:
        return Response("Group {} has been deleted".format(groupname), status=HTTP_200_OK)
    elif resp == 1:
        return Response("Deletion of group'{}' has failed".format(groupname),
                        status=HTTP_400_BAD_REQUEST)
    else:
        return Response("Deletion of group'{}' is still pending".format(groupname),
                        status=HTTP_202_ACCEPTED)


def delete_user(request, username):
    """Delete a user"""
    user_db = User.find(username)
    if not user_db:
        return Response(
            u"User {} doesn't exist".format(username), status=HTTP_404_NOT_FOUND
        )
        
    payload_json = {
        "obj": {"login": username},
        "meta": {"sender": request.user.login}
    }
    
    notif = delete_user_request(PayloadDeleteUserRequest(payload_json))
    resp = wait_response(notif.req_id)

    if resp == 0:
        return Response("User {} has been deleted".format(username), status=HTTP_200_OK)
    elif resp == 1:
        return Response("Deletion of user'{}' has failed".format(username),
                        status=HTTP_400_BAD_REQUEST)
    else:
        return Response("Deletion of user'{}' is still pending".format(username),
                        status=HTTP_202_ACCEPTED)


@api_view(["GET", "DELETE", "PUT"])
@authentication_classes((CassandraAuthentication,))
@permission_classes((IsAuthenticated,))
def group(request, groupname):
    """REST calls to manage a group"""
    if request.method == "GET":
        return ls_group(groupname)
    elif request.method == "DELETE":
        if request.user and request.user.administrator:
            return delete_group(request, groupname)
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


def ls_group(groupname):
    """Get a list of groups"""
    group_db = Group.find(groupname)
    try:
        return Response(group_db.to_dict())
    except NameError:
        return Response(
            u"Group {} not found".format(groupname), status=HTTP_404_NOT_FOUND
        )


def ls_user(username):
    """List user info"""
    user_db = User.find(username)
    if user_db:
        return Response(user_db.to_dict(), status=HTTP_200_OK)
    else:
        return Response(
            u"User {} not found".format(username), status=HTTP_404_NOT_FOUND
        )


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
        return add_user_group(request, group_db, request_body["add_users"])
    # Remove users from group
    if "rm_users" in request_body:
        return rm_user_group(request, group_db, request_body["rm_users"])

    return Response("Bad request", status=HTTP_400_BAD_REQUEST)


def modify_user(request, username):
    """Expecting json in the body:
    { "login": username,
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
    user_db = User.find(username)
    if not user_db:
        return Response(
            u"User {} doesn't exist".format(username), status=HTTP_404_NOT_FOUND
        )
        
    obj = {"login": user_db.login}
    
    if "email" in request_body:
        obj["email"] = request_body.get("email")
    if "password" in request_body:
        obj["password"] = request_body.get("password")
    if "administrator" in request_body:
        obj["administrator"] = request_body.get("administrator")
    if "active" in request_body:
        obj["active"] = request_body.get("active")
    if "ldap" in request_body:
        obj["ldap"] = request_body.get("ldap")
    if "fullname" in request_body:
        obj["fullname"] = request_body.get("fullname")
    
    
    payload_json = {
        "obj": obj,
        "meta": {"sender": request.user.login}
    }
    
    notif = update_user_request(PayloadUpdateUserRequest(payload_json))
    resp = wait_response(notif.req_id)

    if resp == 0:
        user_db = User.find(username)
        return Response(user_db.to_dict(), status=HTTP_200_OK)
    elif resp == 1:
        return Response("Modification of user'{}' has failed".format(user_db.login),
                        status=HTTP_400_BAD_REQUEST)
    else:
        return Response("Modification of user'{}' is still pending".format(user_db.login),
                        status=HTTP_202_ACCEPTED)


def rm_user_group(request, group_db, ls_users):
    """Remove a user (or a list of users) from a group"""
    new_members = list(set(group_db.get_members()) - set(ls_users))
    payload_json = {
        "obj": {
            "name": group_db.name,
            "members": new_members
        }, 
        "meta": {"sender": request.user.login}
    }

    notif = update_group_request(PayloadUpdateGroupRequest(payload_json))
    resp = wait_response(notif.req_id)

    if resp == 0:
        return Response(group_db.to_dict(), status=HTTP_200_OK)
    elif resp == 1:
        return Response("Modification of group'{}' has failed".format(group_db.name),
                        status=HTTP_400_BAD_REQUEST)
    else:
        return Response("Modification of group'{}' is still pending".format(group_db.name),
                        status=HTTP_202_ACCEPTED)


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
            return delete_user(request, username)
        else:
            return Response(MSG_LACK_AUTHORIZATION, status=HTTP_403_FORBIDDEN)
    else:
        return Response(MSG_METH_NOT_ALLOWED, status=HTTP_405_METHOD_NOT_ALLOWED)


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
