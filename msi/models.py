from django.db import models


from radon.model import (
    Collection, 
    Group,
    Resource,
    User
)
import radon
from radon.model.notification import (
    Notification
)
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


def msi_create_collection(payload):
    if "meta" not in payload:
        payload['meta'] = {}
    sender = payload_check(P_META_SENDER, payload)
    if not sender:
        payload['meta']['sender'] = radon.cfg.sys_lib_user
    missing = []
    if not payload_check(P_OBJ_NAME, payload):
        missing.append("name")
    if not payload_check(P_OBJ_CONTAINER, payload):
        missing.append("container")
    if missing:
        msg = MSG_INFO_MISSING.format("collection", ", ".join(missing))
        payload['meta']['msg'] = msg
        Notification.create_fail_collection(payload)
        return { "err": True, "msg" : msg}
    
    obj = payload_check("/obj", payload)
    if not obj:
        msg = MSG_MISSING_OBJ
        Notification.create_fail_collection(payload, msg)
        return { "err": True, "msg" : msg}
        
    coll = Collection.create(**obj)
    
    if coll:
        return { "err": False, "msg" : "Collection created"}
    else:
        return { "err": True, "msg" : "Collection not created"}


def msi_create_resource(payload):
    if "meta" not in payload:
        payload['meta'] = {}
    sender = payload_check(P_META_SENDER, payload)
    if not sender:
        payload['meta']['sender'] = radon.cfg.sys_lib_user
    missing = []
    if not payload_check(P_OBJ_NAME, payload):
        missing.append("name")
    if not payload_check(P_OBJ_CONTAINER, payload):
        missing.append("container")
    if missing:
        msg = MSG_INFO_MISSING.format("resource", ", ".join(missing))
        payload['meta']['msg'] = msg
        Notification.create_fail_resource(payload)
        return { "err": True, "msg" : msg}
    
    obj = payload_check("/obj", payload)
    if not obj:
        msg = MSG_MISSING_OBJ
        Notification.create_fail_resource(payload, msg)
        return { "err": True, "msg" : msg}
    
    resc = Resource.create(**obj)
    
    if resc:
        return { "err": False, "msg" : "Resource created"}
    else:
        return { "err": True, "msg" : "Resource not created"}


def msi_create_group(payload):
    if "meta" not in payload:
        payload['meta'] = {}
    sender = payload_check(P_META_SENDER, payload)
    if not sender:
        payload['meta']['sender'] = radon.cfg.sys_lib_user
    missing = []
    if not payload_check(P_OBJ_NAME, payload):
        missing.append("name")
    if missing:
        msg = MSG_INFO_MISSING.format("group", ", ".join(missing))
        payload['meta']['msg'] = msg
        Notification.create_fail_group(payload)
        return { "err": True, "msg" : msg}
    
    obj = payload_check("/obj", payload)
    if not obj:
        msg = MSG_MISSING_OBJ
        Notification.create_fail_group(payload, msg)
        return { "err": True, "msg" : msg}
    
    group = Group.create(**obj)
    
    if group:
        return { "err": False, "msg" : "Group created"}
    else:
        return { "err": True, "msg" : "Group not created"}


def msi_create_user(payload):
    if "meta" not in payload:
        payload['meta'] = {}
    sender = payload_check(P_META_SENDER, payload)
    if not sender:
        payload['meta']['sender'] = radon.cfg.sys_lib_user
    missing = []
    if not payload_check(P_OBJ_LOGIN, payload):
        missing.append("login")
    if not payload_check("/obj/password", payload):
        missing.append("password")
    if missing:
        msg = MSG_INFO_MISSING.format("user", ", ".join(missing))
        payload['meta']['msg'] = msg
        Notification.create_fail_user(payload)
        return { "err": True, "msg" : msg}
    
    obj = payload_check("/obj", payload)
    if not obj:
        msg = MSG_MISSING_OBJ
        Notification.create_fail_user(payload, msg)
        return { "err": True, "msg" : msg}
    
    user = User.create(**obj)
    
    if user:
        return { "err": False, "msg" : "User created"}
    else:
        return { "err": True, "msg" : "User not created"}


def msi_delete_collection(payload):
    if "meta" not in payload:
        payload['meta'] = {}
    sender = payload_check(P_META_SENDER, payload)
    if not sender:
        payload['meta']['sender'] = radon.cfg.sys_lib_user
    missing = []
    if not payload_check(P_OBJ_NAME, payload):
        missing.append("name")
    if not payload_check(P_OBJ_CONTAINER, payload):
        missing.append("container")
    if missing:
        msg = MSG_INFO_MISSING.format("collection", ", ".join(missing))
        payload['meta']['msg'] = msg
        Notification.delete_fail_collection(payload)
        return { "err": True, "msg" : msg}
    
    obj = payload_check("/obj", payload)
    if not obj:
        msg = MSG_MISSING_OBJ
        Notification.delete_fail_collection(payload, msg)
        return { "err": True, "msg" : msg}
    
    coll = Collection.find(merge(payload_check(P_OBJ_CONTAINER, payload),
                                 payload_check(P_OBJ_NAME, payload)))
    if coll:
        params = {}
        params['sender'] = payload_check(P_META_SENDER, payload, radon.cfg.sys_lib_user)

        coll.delete(**params)
        
        return { "err": False, "msg" : "Collection deleted"}
    else:
        return { "err": True, "msg" : "Collection not deleted"}


def msi_delete_group(payload):
    if "meta" not in payload:
        payload['meta'] = {}
    sender = payload_check(P_META_SENDER, payload)
    if not sender:
        payload['meta']['sender'] = radon.cfg.sys_lib_user
    missing = []
    if not payload_check(P_OBJ_NAME, payload):
        missing.append("name")
    if missing:
        msg = MSG_INFO_MISSING.format("group", ", ".join(missing))
        payload['meta']['msg'] = msg
        Notification.delete_fail_group(payload)
        return { "err": True, "msg" : msg}
    
    obj = payload_check("/obj", payload)
    if not obj:
        msg = MSG_MISSING_OBJ
        payload['meta']['msg'] = msg
        Notification.delete_fail_group(payload)
        return { "err": True, "msg" : msg}
    
    group = Group.find(payload_check(P_OBJ_NAME, payload))
    
    if group:
        params = {}
        params['sender'] = payload_check(P_META_SENDER, payload, radon.cfg.sys_lib_user)

        group.delete(**params)
         
        return { "err": False, "msg" : "Group deleted"}
    else:
        return { "err": True, "msg" : "Group not deleted"}


def msi_delete_resource(payload):
    if "meta" not in payload:
        payload['meta'] = {}
    sender = payload_check(P_META_SENDER, payload)
    if not sender:
        payload['meta']['sender'] = radon.cfg.sys_lib_user
    missing = []
    if not payload_check(P_OBJ_NAME, payload):
        missing.append("name")
    if not payload_check(P_OBJ_CONTAINER, payload):
        missing.append("container")
    if missing:
        msg = MSG_INFO_MISSING.format("resource", ", ".join(missing))
        payload['meta']['msg'] = msg
        Notification.delete_fail_resource(payload)
        return { "err": True, "msg" : msg}
    
    obj = payload_check("/obj", payload)
    if not obj:
        msg = MSG_MISSING_OBJ
        Notification.delete_fail_resource(payload, msg)
        return { "err": True, "msg" : msg}
    
    resc = Resource.find(merge(payload_check(P_OBJ_CONTAINER, payload),
                               payload_check(P_OBJ_NAME, payload)))
    if resc:
        params = {}
        params['sender'] = payload_check(P_META_SENDER, payload, radon.cfg.sys_lib_user)

        resc.delete(**params)
        
        return { "err": False, "msg" : "Collection deleted"}
    else:
        return { "err": True, "msg" : "Collection not deleted"}


def msi_delete_user(payload):
    if "meta" not in payload:
        payload['meta'] = {}
    sender = payload_check(P_META_SENDER, payload)
    if not sender:
        payload['meta']['sender'] = radon.cfg.sys_lib_user
    missing = []
    if not payload_check(P_OBJ_LOGIN, payload):
        missing.append("login")
    if missing:
        msg = MSG_INFO_MISSING.format("user", ", ".join(missing))
        payload['meta']['msg'] = msg
        Notification.delete_fail_user(payload)
        return { "err": True, "msg" : msg}
    
    obj = payload_check("/obj", payload)
    if not obj:
        msg = MSG_MISSING_OBJ
        payload['meta']['msg'] = msg
        Notification.delete_fail_user(payload)
        return { "err": True, "msg" : msg}
    
    user = User.find(payload_check(P_OBJ_LOGIN, payload))
    if user:
        params = {}
        params['sender'] = payload_check(P_META_SENDER, payload, radon.cfg.sys_lib_user)

        user.delete(**params)
         
        return { "err": False, "msg" : "User deleted"}
    else:
        return { "err": True, "msg" : "User not deleter"}


def msi_update_collection(payload):
    if "meta" not in payload:
        payload['meta'] = {}
    sender = payload_check(P_META_SENDER, payload)
    if not sender:
        payload['meta']['sender'] = radon.cfg.sys_lib_user
    missing = []
    if not payload_check(P_OBJ_NAME, payload):
        missing.append("name")
    if not payload_check(P_OBJ_CONTAINER, payload):
        missing.append("container")
    if missing:
        msg = MSG_INFO_MISSING.format("collection", ", ".join(missing))
        payload['meta']['msg'] = msg
        Notification.update_fail_collection(payload)
        return { "err": True, "msg" : msg}
    
    obj = payload_check("/obj", payload)
    if not obj:
        msg = MSG_MISSING_OBJ
        payload['meta']['msg'] = msg
        
        Notification.update_fail_collection(payload)
        return { "err": True, "msg" : msg}
    
    coll = Collection.find(merge(payload_check(P_OBJ_CONTAINER, payload),
                                 payload_check(P_OBJ_NAME, payload)))
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
            
        params['sender'] = payload_check(P_META_SENDER, payload, radon.cfg.sys_lib_user)

        coll.update(**params)
    
        return { "err": False, "msg" : "Collection updated"}
    else:
        return { "err": True, "msg" : "Collection not updated"}


def msi_update_resource(payload):
    if "meta" not in payload:
        payload['meta'] = {}
    sender = payload_check(P_META_SENDER, payload)
    if not sender:
        payload['meta']['sender'] = radon.cfg.sys_lib_user
    missing = []
    if not payload_check(P_OBJ_NAME, payload):
        missing.append("name")
    if not payload_check(P_OBJ_CONTAINER, payload):
        missing.append("container")
    if missing:
        msg = MSG_INFO_MISSING.format("resource", ", ".join(missing))
        payload['meta']['msg'] = msg
        Notification.update_fail_resource(payload)
        return { "err": True, "msg" : msg}
    
    obj = payload_check("/obj", payload)
    if not obj:
        msg = MSG_MISSING_OBJ
        payload['meta']['msg'] = msg
        Notification.update_fail_resource(payload)
        return { "err": True, "msg" : msg}
    
    resc = Resource.find(merge(payload_check(P_OBJ_CONTAINER, payload),
                               payload_check(P_OBJ_NAME, payload)))
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
            
        params['sender'] = payload_check(P_META_SENDER, payload, radon.cfg.sys_lib_user)

        resc.update(**params)
    
        return { "err": False, "msg" : "Resource updated"}
    else:
        return { "err": True, "msg" : "Resource not updated"}


def msi_update_user(payload):
    if "meta" not in payload:
        payload['meta'] = {}
    sender = payload_check(P_META_SENDER, payload)
    if not sender:
        payload['meta']['sender'] = radon.cfg.sys_lib_user
    missing = []
    if not payload_check(P_OBJ_LOGIN, payload):
        missing.append("login")
    if missing:
        msg = MSG_INFO_MISSING.format("user", ", ".join(missing))
        payload['meta']['msg'] = msg
        Notification.update_fail_user(payload)
        return { "err": True, "msg" : msg}
    
    obj = payload_check("/obj", payload)
    if not obj:
        msg = MSG_MISSING_OBJ
        payload['meta']['msg'] = msg
        Notification.update_fail_user(payload)
        return { "err": True, "msg" : msg}
    
    
    user = User.find(payload_check(P_OBJ_LOGIN, payload))
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
        
        params['sender'] = payload_check(P_META_SENDER, payload, radon.cfg.sys_lib_user)

        user.update(**params)
         
        return { "err": False, "msg" : "User updated"}
    else:
        return { "err": True, "msg" : "User not updated"}


def msi_update_group(payload):
    if "meta" not in payload:
        payload['meta'] = {}
    sender = payload_check(P_META_SENDER, payload)
    if not sender:
        payload['meta']['sender'] = radon.cfg.sys_lib_user
    missing = []
    if not payload_check(P_OBJ_NAME, payload):
        missing.append("name")
    if missing:
        msg = MSG_INFO_MISSING.format("group", ", ".join(missing))
        payload['meta']['msg'] = msg
        Notification.update_fail_group(payload)
        return { "err": True, "msg" : msg}
    
    obj = payload_check("/obj", payload)
    if not obj:
        msg = MSG_MISSING_OBJ
        payload['meta']['msg'] = msg
        Notification.update_fail_group(payload)
        return { "err": True, "msg" : msg}
    
    group = Group.find(payload_check(P_OBJ_NAME, payload))
    
    if group:
        params = {}
        params['members'] =  payload_check("/obj/members", payload, group.get_members())
        params['sender'] = payload_check(P_META_SENDER, payload, radon.cfg.sys_lib_user)

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







