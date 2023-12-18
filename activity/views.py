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

from django import template
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.decorators import (
    api_view,
    )
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
)
from radon.model.collection import Collection
from radon.model.group import Group
from radon.model.notification import Notification
from radon.model.resource import Resource
from radon.model.user import User
from radon.model.notification import (
    OP_CREATE,
    OP_DELETE,
    OP_UPDATE,
    OPT_REQUEST,
    OPT_SUCCESS,
    OPT_FAIL,
    OBJ_RESOURCE,
    OBJ_COLLECTION,
    OBJ_USER,
    OBJ_GROUP,
)

ACTIVITY_TMPL = """
<tr>
  <td>{when}</td>
  <td>{action}</td>
  <td>{action_type}</td>
  <td>{object_key}</td>
  <td>{user}</td>
  <td>{msg}</td>
</tr>"""




@login_required
def home(request):
    """Default view for Activities"""    
    notifications = Notification.recent(20)
    activities = []
    for notif in notifications:
        obj_key = notif.get("object_key", "")
        obj = None
        obj_type = notif.get("object_type", "")
        op_name = notif.get("operation_name", "")
        payload = notif.get("payload", {})
        if obj_type == OBJ_RESOURCE:
            obj = Resource.find(obj_key)
            if obj:
                object_dict = obj.to_dict()
            else:
                object_dict = {"name": obj_key}
        elif obj_type == OBJ_COLLECTION:
            obj = Collection.find(obj_key)
            if obj:
                object_dict = obj.to_dict()
            else:
                object_dict = {"name": obj_key}
        elif obj_type == OBJ_USER:
            obj = User.find(obj_key)
            if obj:
                object_dict = obj.to_dict()
            else:
                # User has been deleted it can't be find by uuid
                # look in payload of the message to get the name
                if op_name in [OP_CREATE, OP_DELETE]:
                    name = payload["obj"]["name"]
                elif op_name in [OP_UPDATE]:
                    name = payload["pre"]["name"]
                else:
                    name="ERROR"
                object_dict = {"name": name}
        elif notif["object_type"] == OBJ_GROUP:
            obj = Group.find(obj_key)
            if obj:
                object_dict = obj.to_dict()
            else:
                # User has been deleted it can't be find by uuid
                # look in payload of the message to get the name
                if notif["operation"] in [OP_CREATE, OP_DELETE]:
                    name = payload["obj"]["name"]
                else:  # OP_UPDATE
                    name = payload["pre"]["name"]
                object_dict = {"uuid": obj_key, "name": name}
        user_dict = {}
        if notif["sender"]:
            user = User.find(notif["sender"])
            if user:
                user_dict = user.to_dict()
            else:
                user_dict = { 'name': notif["sender"], 
                              'email': notif["sender"]+ '@radon.org' }
        
        # Create the line 
        tmpl_str = ACTIVITY_TMPL.format(
            when=notif['date'],
            action=notif.get("operation_name", "undefined"),
            action_type=notif.get("operation_type", "undefined"),
            object_key=notif.get("object_key", "undefined"),
            user=notif.get("sender", "undefined"),
            msg=payload)
        
        tmpl = template.Template(tmpl_str)
        variables = {"user": user_dict, "when": notif["when"], "object": object_dict}
        ctx = template.Context(variables)
        activities.append({"html": tmpl.render(ctx)})

    return render(request, "activity/index.html", {"activities": activities})


@api_view(["POST"])
def notification(request):
    messages.add_message(request, messages.INFO, "Hello world.")

    return Response(u"Notification has been received", status=HTTP_200_OK)

