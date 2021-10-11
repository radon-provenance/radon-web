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

from django.urls import path
# 
from archive.views import (
    delete_collection,
    delete_resource,
    download,
    edit_collection,
    edit_resource,
    home,
    new_collection,
    new_reference,
    new_resource,
    preview,
    search,
    view_collection,
    view_resource,
)


app_name = "archive"

urlpatterns = [
    path("", home, name="home"),
    path("search", search, name="search"),
    path("resource<path:path>", view_resource, name="resource_view"),
    path("resource", view_resource, name="resource_view"),
    path("new/collection<path:parent>", new_collection, name="new_collection"),
    path("edit/collection<path:path>", edit_collection, name="edit_collection"),
    path("delete/collection<path:path>", delete_collection, name="delete_collection"),
    path("new/resource<path:parent>", new_resource, name="new_resource"),
    path("edit/resource<path:path>", edit_resource, name="edit_resource"),
    path("delete/resource<path:path>", delete_resource, name="delete_resource"),
    path("view<path:path>", view_collection, name="view"),
    path("view", view_collection, name="view"),
    path("download<path:path>", download, name="download"),
    path("preview<path:path>", preview, name="preview"),
]
