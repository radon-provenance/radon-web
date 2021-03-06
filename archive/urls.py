"""Copyright 2019 - 

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from django.conf.urls import url

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
    search2,
    view_collection,
    view_resource,
)


app_name = "archive"

urlpatterns = [
    url(r"^$", home, name="home"),
    url(r"^search$", search, name="search"),
    url(r"^search2$", search2, name="search2"),
    url(r"^resource(?P<path>.*)$", view_resource, name="resource_view"),
    url(r"^new/collection(?P<parent>.*)$", new_collection, name="new_collection"),
    url(r"^edit/collection(?P<path>.*)$", edit_collection, name="edit_collection"),
    url(
        r"^delete/collection(?P<path>.*)$", delete_collection, name="delete_collection"
    ),
    url(r"^new/resource(?P<parent>.*)$", new_resource, name="new_resource"),
    url(r"^new/reference(?P<parent>.*)$", new_reference, name="new_reference"),
    url(r"^edit/resource(?P<path>.*)$", edit_resource, name="edit_resource"),
    url(r"^delete/resource(?P<path>.*)$", delete_resource, name="delete_resource"),
    url(r"^view(?P<path>.*)$", view_collection, name="view"),
    url(r"^download(?P<path>.*)$", download, name="download"),
    url(r"^preview(?P<path>.*)$", preview, name="preview"),
]
