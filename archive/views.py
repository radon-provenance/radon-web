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
import requests
from django.http import (
    StreamingHttpResponse,
    Http404,
    HttpResponse,
)
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from project.config import (
    ARCHIVE_VIEW,
    URL_DELETE_COLLECTION,
    URL_DELETE_RESOURCE,
    URL_EDIT_COLLECTION,
    URL_EDIT_RESOURCE,
    URL_NEW_COLLECTION,
    URL_NEW_REFERENCE,
    URL_NEW_RESOURCE,
    URL_PREVIEW_RESOURCE,
    URL_VIEW_RESOURCE
) 
from archive.forms import (
    CollectionForm,
    CollectionNewForm,
    ResourceForm,
    ResourceNewForm,
)
from radon.model.collection import Collection
from radon.model.group import Group
from radon.model.notification import (
    create_collection_request,
    create_resource_request,
    delete_collection_request,
    delete_resource_request,
    update_collection_request,
    update_resource_request,
    wait_response,
)
from radon.model.payload import (
    PayloadCreateCollectionRequest,
    PayloadCreateResourceRequest,
    PayloadDeleteCollectionRequest,
    PayloadDeleteResourceRequest,
    PayloadUpdateCollectionRequest,
    PayloadUpdateResourceRequest,
)

from radon.model.resource import Resource
from radon.model.search import Search
from radon.model.errors import (
    ResourceConflictError
)
from radon.util import (
    merge,
    new_request_id,
)


MSG_NAME_CONFLICT = "That name is in use in the current collection"


@login_required
def delete_collection(request, path):
    """Display the page to delete a collection"""
    coll = Collection.find(path)
    if not coll:
        raise Http404
 
    if not coll.user_can(request.user, "delete"):
        raise PermissionDenied
 
    if request.method == "POST":
        parent_coll = Collection.find(coll.path)
        if parent_coll:
            parent_path = parent_coll.container
        else:
            # Just in case
            parent_path = ""
        
        notif = delete_collection_request(PayloadDeleteCollectionRequest.default(coll.path, request.user.login))
        resp = wait_response(notif.req_id)

        if resp == 0:
            msg = "Collection '{}' has been deleted".format(path)
        elif resp == 1:
            msg = "Deletion of collection '{}' has failed".format(path)
        else:
            msg = "Deletion of collection '{}' is still pending".format(path)
        
        messages.add_message(request, messages.INFO, msg)
        
            
        return redirect(ARCHIVE_VIEW, path=parent_path)
 
    return render(request, URL_DELETE_COLLECTION, {"collection": coll})


@login_required
def delete_resource(request, path):
    """Display the page to delete a resource"""
    resc = Resource.find(path)
    if not resc:
        raise Http404
 
    if not resc.user_can(request.user, "delete"):
        raise PermissionDenied
 
    container = Collection.find(resc.container)
    if request.method == "POST":
        notif = delete_resource_request(
            PayloadDeleteResourceRequest.default(resc.path, request.user.login))
        resp = wait_response(notif.req_id)

        if resp == 0:
            msg = "Resource '{}' has been deleted".format(path)
        elif resp == 1:
            msg = "Deletion of resource'{}' has failed".format(path)
        else:
            msg = "Deletion of resource '{}' is still pending".format(path)
        
        messages.add_message(request, messages.INFO, msg)
        
        return redirect(ARCHIVE_VIEW, path=container.path)
 
    # Requires delete on resource
    ctx = {
        "resource": resc,
        "container": container,
    }
 
    return render(request, URL_DELETE_RESOURCE, ctx)


def download(request, path):
    """ Download the content of a resource"""
    resource = Resource.find(path)
    if not resource:
        raise Http404
 
    if not resource.user_can(request.user, "read"):
        raise PermissionDenied

    if resource.is_reference():
        r = requests.get(resource.url, stream=True)
        resp = StreamingHttpResponse(
            streaming_content=r, content_type=resource.get_mimetype()
        )
    else:
        resp = StreamingHttpResponse(
            streaming_content=resource.chunk_content(),
            content_type=resource.get_mimetype(),
        )
    resp["Content-Disposition"] = u'attachment; filename="{}"'.format(resource.name)
 
    return resp


@login_required
def edit_collection(request, path):
    """Display the form to edit an existing collection"""
    coll = Collection.find(path)
    if not coll:
        raise Http404
 
    if not coll.user_can(request.user, "edit"):
        raise PermissionDenied
 
    if request.method == "POST":
        form = CollectionForm(request.POST)
        if form.is_valid():
            metadata = parse_metadata(form.cleaned_data["metadata"])
            data = form.cleaned_data

            payload_json = {
                "obj": {
                    "path": coll.path,
                    "metadata": metadata,
                    "read_access": data["read_access"],
                    "write_access": data["write_access"]
                },
                "meta": {
                    "sender": request.user.login,
                }
            }

            notif = update_collection_request(PayloadUpdateCollectionRequest(payload_json))
            resp = wait_response(notif.req_id)

            if resp == 0:
                msg = "Collection '{}' has been updated".format(path)
            elif resp == 1:
                msg = "Modification of collection '{}' has failed".format(path)
            else:
                msg = "Modification of collection '{}' is still pending".format(path)
            
            messages.add_message(request, messages.INFO, msg)
            
            return redirect(ARCHIVE_VIEW, path=coll.path)
    else:
        md = coll.get_cdmi_user_meta()
        metadata = json.dumps(md)
        if not md:
            metadata = '{"":""}'
        read_access, write_access = coll.get_acl_list()
        initial_data = {
            "name": coll.name,
            "metadata": metadata,
            "read_access": read_access,
            "write_access": write_access,
        }
        form = CollectionForm(initial=initial_data)
 
    groups = Group.objects.all()
    return render(
        request,
        URL_EDIT_COLLECTION,
        {"form": form, "collection": coll, "groups": groups},
    )


@login_required
def edit_resource(request, path):
    """Display the form to edit an existing resource"""
    # Requires edit on resource
    resc = Resource.find(path)
    if not resc:
        raise Http404()
 
    container = Collection.find(resc.container)
    if not container:
        raise Http404()
 
    if not resc.user_can(request.user, "edit"):
        raise PermissionDenied
 
    if request.method == "POST":
        form = ResourceForm(request.POST)
        if form.is_valid():
            metadata = parse_metadata(form.cleaned_data["metadata"])
            data = form.cleaned_data

            payload_json = {
                "obj": {
                    "path": resc.path,
                    "metadata": metadata,
                    "read_access": data["read_access"],
                    "write_access": data["write_access"]
                },
                "meta": {"sender": request.user.login}
            }
            
            notif = update_resource_request(PayloadUpdateResourceRequest(payload_json))
            resp = wait_response(notif.req_id)

            if resp == 0:
                msg = "Resource '{}' has been updated".format(path)
            elif resp == 1:
                msg = "Modification of resource '{}' has failed".format(path)
            else:
                msg = "Modification of resource '{}' is still pending".format(path)
            
            messages.add_message(request, messages.INFO, msg)
            
            return redirect("archive:resource_view", path=resc.path)
    else:
        md = resc.get_cdmi_user_meta()
        metadata = json.dumps(md)
        if not md:
            metadata = '{"":""}'
 
        read_access, write_access = resc.get_acl_list()
        initial_data = {
            "name": resc.name,
            "metadata": metadata,
            "read_access": read_access,
            "write_access": write_access,
        }
        form = ResourceForm(initial=initial_data)
 
    ctx = {
        "form": form,
        "resource": resc,
        "container": container,
        "groups": Group.objects.all(),
    }
 
    return render(request, URL_EDIT_RESOURCE, ctx)


@login_required()
def home(request):
    """Display the root of the archive"""
    return redirect(ARCHIVE_VIEW)


@login_required
def new_collection(request, parent):
    """Display the form to create a new collection"""
    parent_collection = Collection.find(parent)
 
    if not parent_collection.user_can(request.user, "write"):
        raise PermissionDenied
 
    read_access, write_access = parent_collection.get_acl_list()
    initial = {
        "metadata": {},
        "read_access": read_access,
        "write_access": write_access,
    }
    form = CollectionNewForm(request.POST or None, initial=initial)
    if request.method == "POST":
        if form.is_valid():
            data = form.cleaned_data
            try:
                name = data["name"]
                parent = parent_collection.path
                metadata = parse_metadata(form.cleaned_data["metadata"])
                path = merge(parent, name)
                if Collection.find(path + '/'):
                    messages.add_message(
                        request,
                        messages.ERROR,
                        MSG_NAME_CONFLICT,
                    )
                    return render(request, URL_NEW_COLLECTION,
                                  {"form": form, "parent": parent_collection, "groups": Group.objects.all()})
                if Resource.find(path):
                    messages.add_message(
                        request,
                        messages.ERROR,
                        MSG_NAME_CONFLICT,
                    )
                    return render(request, URL_NEW_COLLECTION, 
                                  {"form": form, "parent": parent_collection, "groups": Group.objects.all()})

                payload_json = {
                    "obj": {
                        "name" : name,
                        "container": parent,
                        "path": path,
                        "metadata": metadata,
                        "read_access": data["read_access"],
                        "write_access": data["write_access"]
                    },
                    "meta": {"sender": request.user.login}
                }
                
                notif = create_collection_request(PayloadCreateCollectionRequest(payload_json))
                resp = wait_response(notif.req_id)
    
                if resp == 0:
                    msg = "Collection '{}' has been created".format(path)
                elif resp == 1:
                    msg = "Creation of collection '{}' has failed".format(path)
                else:
                    msg = "Creation of collection '{}' is still pending".format(path)
                
                messages.add_message(request, messages.INFO, msg)
                return redirect(ARCHIVE_VIEW, path=parent)
                
            
            except ResourceConflictError:
                messages.add_message(
                    request,
                    messages.ERROR,
                    MSG_NAME_CONFLICT,
                )
        else:
            return render(request, URL_NEW_COLLECTION,
                          {"form": form, 
                           "parent": parent_collection, 
                           "groups": Group.objects.all()})
    return render(
        request,
        URL_NEW_COLLECTION,
        {"form": form, "parent": parent_collection, "groups": Group.objects.all()},
    )


@login_required
def new_reference(request, parent):
    """Manage the forms to create a new reference resource"""
    parent_collection = Collection.find(parent)
    # Inherits perms from container by default.
    if not parent_collection:
        raise Http404()

    # User must be able to write to this collection
    if not parent_collection.user_can(request.user, "write"):
        raise PermissionDenied

    read_access, write_access = parent_collection.get_acl_list()
    initial = {
        "metadata": {},
        "read_access": read_access,
        "write_access": write_access,
    }

    if request.method == "POST":
        form = ReferenceNewForm(request.POST, initial=initial)
        if form.is_valid():
            data = form.cleaned_data
            try:
                url = data["url"]
                name = data["name"]
                metadata = parse_metadata(form.cleaned_data["metadata"])

                resource = Resource.create(
                    container=parent_collection.path,
                    name=name,
                    metadata=metadata,
                    url=url,
                    sender=request.user.login,
                )
                resource.create_acl_list(data["read_access"], data["write_access"])
                messages.add_message(
                    request,
                    messages.INFO,
                    u"New resource '{}' created".format(resource.get_name()),
                )
            except ResourceConflictError:
                messages.add_message(
                    request,
                    messages.ERROR,
                    "That name is in use within the current collection",
                )

            return redirect(ARCHIVE_VIEW, path=parent_collection.path)
    else:
        form = ReferenceNewForm(initial=initial)

    ctx = {"form": form, "container": parent_collection, "groups": Group.objects.all()}
    return render(request, URL_NEW_REFERENCE, ctx)


@login_required
def new_resource(request, parent):
    """Manage the forms to create a new resource"""
    parent_collection = Collection.find(parent)
    # Inherits perms from container by default.
    if not parent_collection:
        raise Http404()
 
    # User must be able to write to this collection
    if not parent_collection.user_can(request.user, "write"):
        raise PermissionDenied
 
    read_access, write_access = parent_collection.get_acl_list()
    initial = {
        "metadata": {},
        "read_access": read_access,
        "write_access": write_access,
    }
 
    if request.method == "POST":
        form = ResourceNewForm(request.POST, files=request.FILES, initial=initial)
        if form.is_valid():
            data = form.cleaned_data
            name = data["name"]
            parent = parent_collection.path
            metadata = parse_metadata(form.cleaned_data["metadata"])
            path = merge(parent, name)
            
            if Collection.find(path + '/'):
                messages.add_message(
                    request,
                    messages.ERROR,
                    MSG_NAME_CONFLICT,
                )
                return render(request, URL_NEW_RESOURCE,
                              {"form": form, "parent": parent_collection, "groups": Group.objects.all()})
            if Resource.find(path):
                messages.add_message(
                    request,
                    messages.ERROR,
                    MSG_NAME_CONFLICT,
                )
                return render(request, URL_NEW_RESOURCE, 
                              {"form": form, "parent": parent_collection, "groups": Group.objects.all()})

            payload_json = {
                "obj": {
                    "name" : name,
                    "container": parent_collection.path,
                    "path": path, 
                    "metadata": metadata,
                    "mimetype": data["file"].content_type,
                    "size": data["file"].size,
                    "read_access": data["read_access"],
                    "write_access": data["write_access"],
                },
                "meta": {
                    "sender": request.user.login,
                }
            }
            
            notif = create_resource_request(PayloadCreateResourceRequest(payload_json))
            resp = wait_response(notif.req_id)

            if resp == 0:
                msg = "Resource '{}' has been created".format(path)
            elif resp == 1:
                msg = "Creation of resource '{}' has failed".format(path)
            else:
                msg = "Creation of resource '{}' is still pending".format(path)
                
            messages.add_message(request, messages.INFO, msg)

            if resp == 0:
                resource = Resource.find(path)
                resource.put(data["file"]) 
            return redirect(ARCHIVE_VIEW, path=parent_collection.path)
        else:
            ctx = {"form": form, "container": parent_collection, "groups": Group.objects.all()}
            return render(request, URL_NEW_RESOURCE, ctx)
    else:
        form = ResourceNewForm(initial=initial)
 
    ctx = {"form": form, "container": parent_collection, "groups": Group.objects.all()}
    return render(request, URL_NEW_RESOURCE, ctx)


def parse_metadata(form_metadata):
    metadata = {}
    for k, v in json.loads(form_metadata):
        if k in metadata:
            if isinstance(metadata[k], list):
                metadata[k].append(v)
            else:
                metadata[k] = [metadata[k], v]
        else:
            metadata[k] = v
    return metadata


@login_required
def preview(request, path):
    """
    Find the preview of the resource with the given ID and deliver it.  This will
    be rendered in the iframe of the resource view page.
    Deprecated for the moment as the iframe isn't working
    """
    resource = Resource.find(path)
    if not resource:
        raise Http404

    container = Collection.find(resource.container)
    if not container:
        # The container has to be there. If not it may be a network
        # issue with Cassandra so we try again before raising an error to the
        # user
        container = Collection.find(resource.container)
        if not container:
            return HttpResponse(
                status=408,
                content="Unable to find parent container '{}'".format(
                    resource.container
                ),
            )

    paths = []
    full = "/"
    for pth in container.path.split("/"):
        if not pth:
            continue
        full = u"{}{}/".format(full, pth)
        paths.append((pth, full))

    data = ""
    if resource.get_mimetype() in PREVIEW_MIMETYPE:
        data = PREVIEW_MIMETYPE.get(resource.get_mimetype())(resource)

    ctx = {
        "resource": resource.full_dict(request.user),
        "container": container,
        "container_path": container.path,
        "collection_paths": paths,
        "content": data
        }

    return render(request, URL_PREVIEW_RESOURCE, ctx)


def preview_test(resource):
    return "test"


def preview_text_json(resource):
    res = ""
    if resource.is_reference():
        res = requests.get(resource.url, stream=True)
    else:
        data = []
        for chk in resource.chunk_content():
            data.append(chk)
        res = b"".join([s for s in data])
        json_obj = json.loads(res)
        res = "<pre>{}</pre>".format(json.dumps(json_obj, indent=2))

    return res


def preview_text_plain(resource):
    res = ""
    if resource.is_reference():
        res = requests.get(resource.url, stream=True)
    else:
        data = []
        for chk in resource.chunk_content():
            data.append(chk)
        res = b"".join([s for s in data])
        res = "<pre>{}</pre>".format(res)

    return res


def search(request):
    """Display the search results page"""
    query = request.GET.get("q")
    collection = request.GET.get("collection")
    
    ctx = {"q": query}
    
    if ":" not in query:
        solr_query = """solr_query='path:"{}"'""".format(query)
    else:
        solr_query = """solr_query='{}'""".format(query)
    
    results = Search.search(solr_query, request.user)
    
    if collection:
        results = [el for el in results if el["path"].startswith(collection)]
    
    ctx["results"] = results
    ctx["total"] = len(ctx["results"])
 
    return render(request, "archive/search.html", ctx)


@login_required()
def view_collection(request, path='/'):
    """Display the page which shows the subcollections/resources of a collection"""
    if not path:
        path = "/"
    collection = Collection.find(path)

    if not collection:
        raise Http404()
 
    if not collection.user_can(request.user, "read") and not collection.is_root:
        # If the user can't read, then return 404 rather than 403 so that
        # we don't leak information.
        raise Http404()

    paths = []
    full = "/"
    for p in collection.path.split("/"):
        if not p:
            continue
        full = u"{}{}/".format(full, p)
        paths.append((p, full))
 
    children_c, children_r = collection.get_child(False)
    children_c.sort(key=lambda x: x.lower())
    children_r.sort(key=lambda x: x.lower())
    
    # With pending requests it may be possible that some objects are currently being deleted
    ls_coll = []
    for c in children_c:
        child_c = Collection.find(merge(path, c))
        if child_c:
            ls_coll.append(child_c.to_dict(request.user))
    ls_resc = []
    for c in children_r:
        child_r = Resource.find(merge(path, c))
        if child_r:
            ls_resc.append(child_r.simple_dict(request.user))
    ctx = {
        "collection": collection.to_dict(request.user),
        "children_c": ls_coll,
        "children_r": ls_resc,
        "collection_paths": paths,
        "empty": len(ls_coll) + len(ls_resc) == 0,
    }
    return render(request, "archive/index.html", ctx)


@login_required()
def view_resource(request, path):
    """Display the page for a resource in the archive"""
    resource = Resource.find(path)
    if not resource:
        raise Http404()
 
    if not resource.user_can(request.user, "read"):
        raise PermissionDenied
 
    container = Collection.find(resource.container)
    if not container:
        # The container has to be there. If not it may be a network
        # issue with Cassandra so we try again before raising an error to the
        # user
        container = Collection.find(resource.container)
        if not container:
            return HttpResponse(
                status=408,
                content="Unable to find parent container '{}'".format(
                    resource.container
                ),
            )
 
    paths = []
    full = "/"
    for pth in container.path.split("/"):
        if not pth:
            continue
        full = u"{}{}/".format(full, pth)
        paths.append((pth, full))
 
    ctx = {
        "resource": resource.full_dict(request.user),
        "container": container,
        "container_path": container.path,
        "collection_paths": paths,
        "preview": resource.get_mimetype() in PREVIEW_MIMETYPE.keys()
    }
    return render(request, URL_VIEW_RESOURCE, ctx)




PREVIEW_MIMETYPE = {
    "text/json" : preview_text_json,
    "text/plain" : preview_text_plain,
    "test" : preview_test
}
