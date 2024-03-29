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
# 
from archive.forms import (
    CollectionForm,
    CollectionNewForm,
    ResourceForm,
    ResourceNewForm,
)
 
from radon.model import (
    Collection, 
    Group,
    Resource,
    Search
)
from radon.model.errors import (
    CollectionConflictError,
    ResourceConflictError
)
from radon.util import merge



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
        coll.delete(username=request.user.name)
        messages.add_message(
            request,
            messages.INFO,
            u"The collection '{}' has been deleted".format(coll.name),
        )
        return redirect("archive:view", path=parent_path)
 
    return render(request, "archive/delete.html", {"collection": coll})


@login_required
def delete_resource(request, path):
    """Display the page to delete a resource"""
    resource = Resource.find(path)
    if not resource:
        raise Http404
 
    if not resource.user_can(request.user, "delete"):
        raise PermissionDenied
 
    container = Collection.find(resource.container)
    if request.method == "POST":
        resource.delete(username=request.user.name)
        messages.add_message(
            request,
            messages.INFO,
            "The resource '{}' has been deleted".format(resource.name),
        )
        return redirect("archive:view", path=container.path)
 
    # Requires delete on resource
    ctx = {
        "resource": resource,
        "container": container,
    }
 
    return render(request, "archive/resource/delete.html", ctx)


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
                metadata = {}

                for k, v in json.loads(data["metadata"]):
                    if k in metadata:
                        if isinstance(metadata[k], list):
                            metadata[k].append(v)
                        else:
                            metadata[k] = [metadata[k], v]
                    else:
                        metadata[k] = v

                resource = Resource.create(
                    container=parent_collection.path,
                    name=name,
                    metadata=metadata,
                    url=url,
                    username=request.user.name,
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

            return redirect("archive:view", path=parent_collection.path)
    else:
        form = ReferenceNewForm(initial=initial)

    ctx = {"form": form, "container": parent_collection, "groups": Group.objects.all()}
    return render(request, "archive/resource/new_reference.html", ctx)


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
            metadata = {}
            for k, v in json.loads(form.cleaned_data["metadata"]):
                if k in metadata:
                    if isinstance(metadata[k], list):
                        metadata[k].append(v)
                    else:
                        metadata[k] = [metadata[k], v]
                else:
                    metadata[k] = v
 
            try:
                data = form.cleaned_data
                coll.update(metadata=metadata, username=request.user.name)
                coll.create_acl_list(data["read_access"], data["write_access"])
                return redirect("archive:view", path=coll.path)
            except CollectionConflictError:
                messages.add_message(
                    request,
                    messages.ERROR,
                    "That name is in use in the current collection",
                )
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
        "archive/edit.html",
        {"form": form, "collection": coll, "groups": groups},
    )


@login_required
def edit_resource(request, path):
    """Display the form to edit an existing resource"""
    # Requires edit on resource
    resource = Resource.find(path)
    if not resource:
        raise Http404()
 
    container = Collection.find(resource.container)
    if not container:
        raise Http404()
 
    if not resource.user_can(request.user, "edit"):
        raise PermissionDenied
 
    if request.method == "POST":
        form = ResourceForm(request.POST)
        if form.is_valid():
            metadata = {}
            for k, v in json.loads(form.cleaned_data["metadata"]):
                if k in metadata:
                    if isinstance(metadata[k], list):
                        metadata[k].append(v)
                    else:
                        metadata[k] = [metadata[k], v]
                else:
                    metadata[k] = v
            try:
                data = form.cleaned_data
                resource.update(metadata=metadata, username=request.user.name)
                resource.create_acl_list(data["read_access"], data["write_access"])
 
                return redirect("archive:resource_view", path=resource.path)
            except ResourceConflictError:
                messages.add_message(
                    request,
                    messages.ERROR,
                    "That name is in use within the current collection",
                )
    else:
        md = resource.get_cdmi_user_meta()
        metadata = json.dumps(md)
        if not md:
            metadata = '{"":""}'
 
        read_access, write_access = resource.get_acl_list()
        initial_data = {
            "name": resource.name,
            "metadata": metadata,
            "read_access": read_access,
            "write_access": write_access,
        }
        form = ResourceForm(initial=initial_data)
 
    ctx = {
        "form": form,
        "resource": resource,
        "container": container,
        "groups": Group.objects.all(),
    }
 
    return render(request, "archive/resource/edit.html", ctx)


@login_required()
def home(request):
    """Display the root of the archive"""
    return redirect("archive:view")


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
                metadata = {}
 
                for k, v in json.loads(data["metadata"]):
                    if k in metadata:
                        if isinstance(metadata[k], list):
                            metadata[k].append(v)
                        else:
                            metadata[k] = [metadata[k], v]
                    else:
                        metadata[k] = v
 
                collection = Collection.create(
                    name=name,
                    container=parent,
                    metadata=metadata,
                    creator=request.user.name,
                )
                collection.create_acl_list(data["read_access"], data["write_access"])
                
                messages.add_message(
                    request,
                    messages.INFO,
                    u"New collection '{}' created".format(collection.name),
                )
                return redirect("archive:view", path=collection.path)
            except CollectionConflictError:
                messages.add_message(
                    request,
                    messages.ERROR,
                    "That name is in use in the current collection",
                )
            except ResourceConflictError:
                messages.add_message(
                    request,
                    messages.ERROR,
                    "That name is in use in the current collection",
                )
    groups = Group.objects.all()
    return render(
        request,
        "archive/new.html",
        {"form": form, "parent": parent_collection, "groups": groups},
    )


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
            try:
                name = data["name"]
                metadata = {}

                for k, v in json.loads(data["metadata"]):
                    if k in metadata:
                        if isinstance(metadata[k], list):
                            metadata[k].append(v)
                        else:
                            metadata[k] = [metadata[k], v]
                    else:
                        metadata[k] = v

                resource = Resource.create(
                    container=parent_collection.path,
                    name=name,
                    metadata=metadata,
                    mimetype=data["file"].content_type,
                    creator=request.user.name,
                    size=data["file"].size,
                )
                res = resource.put(data["file"])
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
 
            return redirect("archive:view", path=parent_collection.path)
    else:
        form = ResourceNewForm(initial=initial)
 
    ctx = {"form": form, "container": parent_collection, "groups": Group.objects.all()}
    return render(request, "archive/resource/new.html", ctx)


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
 
    preview_info = {
        # "type": "image",
        # "url": "http://....."
    }
 
    return render(request, "archive/preview.html", {"preview": preview_info})


def search(request):
    """Display the search results page"""
    query = request.GET.get("q")
    collection = request.GET.get("collection")
    
    ctx = {"q": query}
    
    if not ":" in query:
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
    
        
    ctx = {
        "collection": collection.to_dict(request.user),
        "children_c": [
            Collection.find(merge(path, c)).to_dict(request.user) for c in children_c
        ],
        "children_r": [
            Resource.find(merge(path, c)).simple_dict(request.user) for c in children_r
        ],
        "collection_paths": paths,
        "empty": len(children_c) + len(children_r) == 0,
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
        # TODO: the container has to be there. If not it may be a network
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
    }
    return render(request, "archive/resource/view.html", ctx)

