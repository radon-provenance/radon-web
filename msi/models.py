from django.db import models

from radon.model.config import cfg
from radon.model.collection import Collection
from radon.model.group import Group
from radon.model.resource import Resource
from radon.model.user import User
from radon.model.notification import (
    create_fail_collection,
    create_fail_resource,
    create_fail_group,
    create_fail_user,
    delete_fail_collection,
    delete_fail_resource,
    delete_fail_group,
    delete_fail_user,
    update_fail_collection,
    update_fail_resource,
    update_fail_group,
    update_fail_user,
)
from radon.model.payload import (
    PayloadCreateRequestCollection,
    PayloadCreateFailCollection,
    PayloadCreateRequestResource,
    PayloadCreateFailResource,
    PayloadCreateRequestGroup,
    PayloadCreateFailGroup,
    PayloadCreateRequestUser,
    PayloadCreateFailUser,
    PayloadDeleteRequestCollection,
    PayloadDeleteFailCollection,
    PayloadDeleteRequestResource,
    PayloadDeleteFailResource,
    PayloadDeleteRequestGroup,
    PayloadDeleteFailGroup,
    PayloadDeleteRequestUser,
    PayloadDeleteFailUser,
    PayloadUpdateRequestCollection,
    PayloadUpdateFailCollection,
    PayloadUpdateRequestResource,
    PayloadUpdateFailResource,
    PayloadUpdateRequestGroup,
    PayloadUpdateFailGroup,
    PayloadUpdateRequestUser,
    PayloadUpdateFailUser,
)
from radon.model.microservices import Microservices
from radon.util import (
    merge,
    payload_check
)



P_META_SENDER = "/meta/sender"
P_OBJ_CONTAINER = "/obj/container"
P_OBJ_NAME = "/obj/name"
P_OBJ_LOGIN = "/obj/login"

MSG_INFO_MISSING = "Information is missing for the {}: {}"
MSG_MISSING_OBJ = "Missing object in payload"


def msi_test(params):
    msg = params.get('msg', '')
    return { "out" : msg * 2}


def msi_create_collection(payload_json):
    payload = PayloadCreateRequestCollection(payload_json)
    
    (is_valid, msg) = payload.validate()
    if not is_valid: # Create valid payload
        payload = PayloadCreateFailCollection.default(
            payload.get_object_key(),
            msg,
            payload.get_sender())
        create_fail_collection(payload)
        return { "err": True, "msg" : msg}
    
    obj = payload_check("/obj", payload_json)
    coll = Collection.create(**obj)
     
    if coll:
        return { "err": False, "msg" : "Collection created"}
    else:
        return { "err": True, "msg" : "Collection not created"}


def msi_create_resource(payload_json):
    payload = PayloadCreateRequestResource(payload_json)
    
    (is_valid, msg) = payload.validate()
    if not is_valid: # Create valid payload
        payload = PayloadCreateFailResource.default(
            payload.get_object_key(),
            msg,
            payload.get_sender())
        create_fail_resource(payload)
        return { "err": True, "msg" : msg}

    obj = payload_check("/obj", payload)
    resc = Resource.create(**obj)
    
    if resc:
        return { "err": False, "msg" : "Resource created"}
    else:
        return { "err": True, "msg" : "Resource not created"}


def msi_create_group(payload_json):
    payload = PayloadCreateRequestGroup(payload_json)
    
    (is_valid, msg) = payload.validate()
    if not is_valid: # Create valid payload
        payload = PayloadCreateFailGroup.default(
            payload.get_object_key(),
            msg,
            payload.get_sender())
        create_fail_group(payload)
        return { "err": True, "msg" : msg}

    obj = payload_check("/obj", payload)
    group = Group.create(**obj)

    if group:
        return { "err": False, "msg" : "Group created"}
    else:
        return { "err": True, "msg" : "Group not created"}


def msi_create_user(payload_json):
    user, msg = Microservices.create_user(PayloadCreateRequestUser(payload_json))
    if user:
        return { "err": False, "msg" : msg}
    else:
        return { "err": True, "msg" : "User not created - " + msg}


def msi_delete_collection(payload_json):
    payload = PayloadDeleteRequestCollection(payload_json)
    
    (is_valid, msg) = payload.validate()
    if not is_valid: # Create valid payload
        payload = PayloadDeleteFailCollection.default(
            payload.get_object_key(),
            msg,
            payload.get_sender())
        delete_fail_collection(payload_json)
        return { "err": True, "msg" : msg}

    coll = Collection.find(payload.get_object_key())
    if coll:
        params = {}
        params['sender'] = payload_check(P_META_SENDER, payload, cfg.sys_lib_user)

        coll.delete(**params)
        
        return { "err": False, "msg" : "Collection deleted"}
    else:
        return { "err": True, "msg" : "Collection not deleted"}


def msi_delete_group(payload_json):
    payload = PayloadDeleteRequestGroup(payload_json)
    
    (is_valid, msg) = payload.validate()
    if not is_valid: # Create valid payload
        payload = PayloadDeleteFailGroup.default(
            payload.get_object_key(),
            msg,
            payload.get_sender())
        delete_fail_group(payload_json)
        return { "err": True, "msg" : msg}

    group = Group.find(payload.get_object_key())
    
    if group:
        params = {}
        params['sender'] = payload_check(P_META_SENDER, payload, cfg.sys_lib_user)

        group.delete(**params)
         
        return { "err": False, "msg" : "Group deleted"}
    else:
        return { "err": True, "msg" : "Group not deleted"}


def msi_delete_resource(payload_json):
    payload = PayloadDeleteRequestResource(payload_json)
    
    (is_valid, msg) = payload.validate()
    if not is_valid: # Create valid payload
        payload = PayloadDeleteFailResource.default(
            payload.get_object_key(),
            msg,
            payload.get_sender())
        delete_fail_resource(payload_json)
        return { "err": True, "msg" : msg}
    
    resc = Resource.find(payload.get_object_key())
    if resc:
        params = {}
        params['sender'] = payload_check(P_META_SENDER, payload, cfg.sys_lib_user)

        resc.delete(**params)
        
        return { "err": False, "msg" : "Collection deleted"}
    else:
        return { "err": True, "msg" : "Collection not deleted"}


def msi_delete_user(payload_json):
    payload = PayloadDeleteRequestUser(payload_json)
    
    (is_valid, msg) = payload.validate()
    if not is_valid: # Create valid payload
        payload = PayloadDeleteFailUser.default(
            payload.get_object_key(),
            msg,
            payload.get_sender())
        delete_fail_user(payload_json)
        return { "err": True, "msg" : msg}
    
    user = User.find(payload.get_object_key())
    if user:
        params = {}
        params['sender'] = payload_check(P_META_SENDER, payload, cfg.sys_lib_user)

        user.delete(**params)
         
        return { "err": False, "msg" : "User deleted"}
    else:
        return { "err": True, "msg" : "User not deleter"}


def msi_update_collection(payload_json):
    payload = PayloadUpdateRequestCollection(payload_json)
    
    (is_valid, msg) = payload.validate()
    if not is_valid: # Create valid payload
        payload = PayloadUpdateFailCollection.default(
            payload.get_object_key(),
            msg,
            payload.get_sender())
        update_fail_collection(payload_json)
        return { "err": True, "msg" : msg}
    
    obj = payload_check("/obj", payload)
    coll = Collection.find(obj.path)
    if coll:
        params = {}
        metadata = payload_check("/obj/metadata", payload, None)
        if metadata != None:
            params['metadata'] = metadata
        read_access = payload_check("/obj/read_access", payload, None)
        if read_access != None:
            params['read_access'] = read_access
        write_access = payload_check("/obj/write_access", payload, None)
        if write_access != None:
            params['write_access'] = write_access
            
        params['sender'] = payload_check(P_META_SENDER, payload, cfg.sys_lib_user)

        coll.update(**params)
    
        return { "err": False, "msg" : "Collection updated"}
    else:
        return { "err": True, "msg" : "Collection not updated"}


def msi_update_resource(payload_json):
    payload = PayloadUpdateRequestResource(payload_json)
    
    (is_valid, msg) = payload.validate()
    if not is_valid: # Create valid payload
        payload = PayloadUpdateFailResource.default(
            payload.get_object_key(),
            msg,
            payload.get_sender())
        update_fail_resource(payload_json)
        return { "err": True, "msg" : msg}
    
    obj = payload_check("/obj", payload)
    resc = Resource.find(obj.path)
    if resc:
        params = {}
        metadata = payload_check("/obj/metadata", payload, None)
        if metadata != None:
            params['metadata'] = metadata
        read_access = payload_check("/obj/read_access", payload, None)
        if read_access != None:
            params['read_access'] = read_access
        write_access = payload_check("/obj/write_access", payload, None)
        if write_access != None:
            params['write_access'] = write_access
            
        params['sender'] = payload_check(P_META_SENDER, payload, cfg.sys_lib_user)

        resc.update(**params)
    
        return { "err": False, "msg" : "Resource updated"}
    else:
        return { "err": True, "msg" : "Resource not updated"}


def msi_update_user(payload_json):
    payload = PayloadUpdateRequestUser(payload_json)
    
    (is_valid, msg) = payload.validate()
    if not is_valid: # Create valid payload
        payload = PayloadUpdateFailUser.default(
            payload.get_object_key(),
            msg,
            payload.get_sender())
        update_fail_user(payload_json)
        return { "err": True, "msg" : msg}
    
    obj = payload_check("/obj", payload)
    user = User.find(obj.login)
    if user:
        params = {}
        email = payload_check("/obj/email", payload)
        if email:
            params['email'] = email
        fullname = payload_check("/obj/fullname", payload)
        if fullname:
            params['fullname'] = fullname
        administrator = payload_check("/obj/administrator", payload, None)
        if administrator != None:
            params['administrator'] = administrator
        active = payload_check("/obj/active", payload, None)
        if active != None:
            params['active'] = active
        ldap = payload_check("/obj/ldap", payload, None)
        if ldap != None:
            params['ldap'] = ldap
        password = payload_check("/obj/password", payload)
        if password:
            params['password'] = password
        
        params['sender'] = payload_check(P_META_SENDER, payload, cfg.sys_lib_user)

        user.update(**params)
         
        return { "err": False, "msg" : "User updated"}
    else:
        return { "err": True, "msg" : "User not updated"}


def msi_update_group(payload_json):
    payload = PayloadUpdateRequestGroup(payload_json)
    
    (is_valid, msg) = payload.validate()
    if not is_valid: # Create valid payload
        payload = PayloadUpdateFailgroup.default(
            payload.get_object_key(),
            msg,
            payload.get_sender())
        update_fail_group(payload_json)
        return { "err": True, "msg" : msg}
    
    obj = payload_check("/obj", payload)
    group = Group.find(obj.name)
    
    if group:
        params = {}
        params['members'] =  payload_check("/obj/members", payload, group.get_members())
        params['sender'] = payload_check(P_META_SENDER, payload, cfg.sys_lib_user)

        group.update(**params)
         
        return { "err": False, "msg" : "User updated"}
    else:
        return { "err": True, "msg" : "User not updated"}



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
                    {"name" : "err", "type" : "bool"},
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
                    {"name" : "err", "type" : "bool"},
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
                    {"name" : "err", "type" : "bool"},
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
                    {"name" : "err", "type" : "bool"},
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
                    {"name" : "err", "type" : "bool"},
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
                    {"name" : "err", "type" : "bool"},
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
                    {"name" : "err", "type" : "bool"},
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
                    {"name" : "err", "type" : "bool"},
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
                    {"name" : "err", "type" : "bool"},
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
                    {"name" : "err", "type" : "bool"},
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
                    {"name" : "err", "type" : "bool"},
                    {"name" : "msg", "type" : "str"}
                ],
        },
        "code" : msi_update_group
    },
    

}







