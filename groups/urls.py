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

from groups.views import (
    add_user,
    delete_group,
    edit_group,
    group_view,
    home,
    new_group,
    rm_user,
)

app_name = "groups"

urlpatterns = [
    path("", home, name="home"),
    path("new", new_group, name="new_group"),
    path("delete/<str:name>", delete_group, name="delete_group"),
    path("edit/<str:name>", edit_group, name="edit_group"),
    path("rm_user/<str:name>/<str:uname>", rm_user, name="rm_user"),
    path("add_user/<str:name>", add_user, name="add_user"),
    path("<str:name>", group_view, name="view"),
]
