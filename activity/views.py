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

import pprint
from django import template
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from radon.model.collection import Collection
from radon.model.group import Group
from radon.model.notification import Notification
from radon.model.resource import Resource
from radon.model.user import User
from radon.model.notification import (
    OP_CREATE,
    OP_DELETE,
    OP_UPDATE,
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
  <td><pre>{msg}</pre></td>
</tr>"""


def get_coll_obj_dict(obj_key):
    """
    Get a dictionary which describes a collection object. If not found returns
    a minimal description.
    
    :param obj_key: The key of the object in Cassandra (path)
    :type obj_key: str
    
    :return: A dictionary with collection fields
    :rtype: dict
    """
    obj = Collection.find(obj_key)
    if obj:
        return obj.to_dict()
    else:
        return {"name": obj_key}


def get_group_obj_dict(obj_key, op_name, payload):
    """
    Get a dictionary which describes a group object. If not found try to find the
    name in the payload or return a minimal description.
    
    :param obj_key: The key of the object in Cassandra (name)
    :type obj_key: str
    
    :return: A dictionary with group fields
    :rtype: dict
    """
    obj = Group.find(obj_key)
    if obj:
        return obj.to_dict()
    else:
        # User has been deleted it can't be find by uuid
        # look in payload of the message to get the name
        name="ERROR"
        try:
            if op_name in [OP_CREATE, OP_DELETE]:
                name = payload["obj"]["name"]
            elif op_name in [OP_UPDATE]:
                name = payload["pre"]["name"]
        except KeyError:
            pass
        return {"name": name}


def get_resc_obj_dict(obj_key):
    """
    Get a dictionary which describes a resource object. If not found returns
    a minimal description.
    
    :param obj_key: The key of the object in Cassandra (path)
    :type obj_key: str
    
    :return: A dictionary with resource fields
    :rtype: dict
    """
    obj = Resource.find(obj_key)
    if obj:
        return obj.to_dict()
    else:
        return {"name": obj_key}


def get_user_obj_dict(obj_key, op_name, payload):
    """
    Get a dictionary which describes a user object. If not found try to find the
    name in the payload or return a minimal description.
    
    :param obj_key: The key of the object in Cassandra (login)
    :type obj_key: str
    
    :return: A dictionary with user fields
    :rtype: dict
    """
    obj = User.find(obj_key)
    if obj:
        return obj.to_dict()
    else:
        # User has been deleted it can't be find by uuid
        # look in payload of the message to get the name
        name="ERROR"
        try:
            if op_name in [OP_CREATE, OP_DELETE]:
                name = payload["obj"]["login"]
            elif op_name in [OP_UPDATE]:
                name = payload["pre"]["login"]
        except KeyError:
            pass
        return {"name": name}


@login_required
def home(request):
    """Default view for Activities"""    
    notifications = Notification.recent(20)
    activities = []
    for notif in notifications:
        obj_key = notif.get("object_key", "")
        obj_type = notif.get("object_type", "")
        op_name = notif.get("operation_name", "")
        payload = notif.get("payload", {})

        if obj_type == OBJ_RESOURCE:
            object_dict = get_resc_obj_dict(obj_key)
        elif obj_type == OBJ_COLLECTION:
            object_dict = get_coll_obj_dict(obj_key)
        elif obj_type == OBJ_USER:
            object_dict = get_user_obj_dict(obj_key, op_name, payload)
        elif obj_type == OBJ_GROUP:
            object_dict = get_group_obj_dict(obj_key, op_name, payload)

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
            msg=pprint.pformat(payload))
        
        tmpl = template.Template(tmpl_str)
        variables = {"user": user_dict, "when": notif["when"], "object": object_dict}
        ctx = template.Context(variables)
        activities.append({"html": tmpl.render(ctx)})

    return render(request, "activity/index.html", {"activities": activities})



