# Radon Copyright 2023, University of Oxford
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

from django.db import models

from radon.model.config import cfg
from radon.model.collection import Collection
from radon.model.group import Group
from radon.model.resource import Resource
from radon.model.user import User
from radon.model.notification import (
    create_collection_fail,
    create_resource_fail,
    create_group_fail,
    create_user_fail,
    delete_collection_fail,
    delete_resource_fail,
    delete_group_fail,
    delete_user_fail,
    update_collection_fail,
    update_resource_fail,
    update_group_fail,
    update_user_fail,
)
from radon.model.payload import (
    PayloadCreateCollectionRequest,
    PayloadCreateCollectionFail,
    PayloadCreateResourceRequest,
    PayloadCreateResourceFail,
    PayloadCreateGroupRequest,
    PayloadCreateGroupFail,
    PayloadCreateUserRequest,
    PayloadCreateUserFail,
    PayloadDeleteCollectionRequest,
    PayloadDeleteCollectionFail,
    PayloadDeleteResourceRequest,
    PayloadDeleteResourceFail,
    PayloadDeleteGroupRequest,
    PayloadDeleteGroupFail,
    PayloadDeleteUserRequest,
    PayloadDeleteUserFail,
    PayloadUpdateCollectionRequest,
    PayloadUpdateCollectionFail,
    PayloadUpdateResourceRequest,
    PayloadUpdateResourceFail,
    PayloadUpdateGroupRequest,
    PayloadUpdateGroupFail,
    PayloadUpdateUserRequest,
    PayloadUpdateUserFail,
)
from radon.model.microservices import Microservices
from radon.util import (
    merge,
    payload_check
)
from radon.model import payload



P_META_SENDER = "/meta/sender"
P_OBJ_CONTAINER = "/obj/container"
P_OBJ_NAME = "/obj/name"
P_OBJ_LOGIN = "/obj/login"

MSG_INFO_MISSING = "Information is missing for the {}: {}"
MSG_MISSING_OBJ = "Missing object in payload"


def msi_test(params):
    msg = params.get('msg', '')
    return {"out" : msg * 2}


def msi_create_collection(payload_json):
    ok, _, msg = Microservices.create_collection(PayloadCreateCollectionRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_create_group(payload_json):
    ok, _, msg = Microservices.create_group(PayloadCreateGroupRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_create_resource(payload_json):
    ok, _, msg = Microservices.create_resource(PayloadCreateResourceRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_create_user(payload_json):
    ok, _, msg = Microservices.create_user(PayloadCreateUserRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_delete_collection(payload_json):
    ok, _, msg = Microservices.delete_collection(PayloadDeleteCollectionRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_delete_group(payload_json):
    ok, _, msg = Microservices.delete_group(PayloadDeleteGroupRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_delete_resource(payload_json):
    ok, _, msg = Microservices.delete_resource(PayloadDeleteResourceRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_delete_user(payload_json):
    ok, _, msg = Microservices.delete_user(PayloadDeleteUserRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_update_collection(payload_json):
    ok, _, msg = Microservices.update_collection(PayloadUpdateCollectionRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_update_group(payload_json):
    ok, _, msg = Microservices.update_group(PayloadUpdateGroupRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_update_resource(payload_json):
    ok, _, msg = Microservices.update_resource(PayloadUpdateResourceRequest(payload_json))
    return {"ok": ok, "msg" : msg}


def msi_update_user(payload_json):
    ok, _, msg = Microservices.update_user(PayloadUpdateUserRequest(payload_json))
    return {"ok": ok, "msg" : msg}



MICROSERVICES = {
    "test" : {
        "definition" : {
            "input" : [
                    {"name" : "msg", "type" : "str"}
                ],
            "output" : [
                    {"name" : "out", "type" : "str"}
                ],
        },
        "code" : msi_test
    },
    
    "create_collection" : {
        "definition" : {
            "input" : [
                    {"name" : "container", "type" : "str", "required" : True},
                    {"name" : "name", "type" : "str", "required" : True},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_create_collection
    },
    
    "create_resource" : {
        "definition" : {
            "input" : [
                    {"name" : "container", "type" : "str", "required" : True},
                    {"name" : "name", "type" : "str", "required" : True},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_create_resource
    },
    
    "create_user" : {
        "definition" : {
            "input" : [
                    {"name" : "login", "type" : "str", "required" : True},
                    {"name" : "email", "type" : "str", "required" : False},
                    {"name" : "password", "type" : "str"},
                    {"name" : "administrator", "type" : "bool"},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_create_user
    },
    
    "create_group" : {
        "definition" : {
            "input" : [
                    {"name" : "name", "type" : "str", "required" : True},
                ],
            "output" : [
                    {"name" : "err", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_create_group
    },
    
    "delete_collection" : {
        "definition" : {
            "input" : [
                    {"name" : "container", "type" : "str", "required" : True},
                    {"name" : "name", "type" : "str", "required" : True},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_delete_collection
    },
    
    "delete_group" : {
        "definition" : {
            "input" : [
                    {"name" : "name", "type" : "str", "required" : True},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_delete_group
    },
    
    "delete_resource" : {
        "definition" : {
            "input" : [
                    {"name" : "container", "type" : "str", "required" : True},
                    {"name" : "name", "type" : "str", "required" : True},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_delete_resource
    },
    
    "delete_user" : {
        "definition" : {
            "input" : [
                    {"name" : "login", "type" : "str", "required" : True},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_delete_user
    },
    
    "update_collection" : {
        "definition" : {
            "input" : [
                    {"name" : "container", "type" : "str", "required" : True},
                    {"name" : "name", "type" : "str", "required" : True},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_update_collection
    },
    
    "update_resource" : {
        "definition" : {
            "input" : [
                    {"name" : "container", "type" : "str", "required" : True},
                    {"name" : "name", "type" : "str", "required" : True},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_update_resource
    },
    
    "update_user" : {
        "definition" : {
            "input" : [
                    {"name" : "login", "type" : "str", "required" : True},
                    {"name" : "email", "type" : "str", "required" : False},
                    {"name" : "fullname", "type" : "str", "required" : False},
                    {"name" : "password", "type" : "str"},
                    {"name" : "administrator", "type" : "bool"},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_update_user
    },
    "update_group" : {
        "definition" : {
            "input" : [
                    {"name" : "name", "type" : "str", "required" : True},
                    {"name" : "members", "type" : "list", "required" : False},
                ],
            "output" : [
                    {"name" : "ok", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_update_group
    },
    

}







