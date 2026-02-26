# Radon Copyright 2025, University of Oxford
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

from . import views

app_name = "administration"

urlpatterns = [
    path("", views.home, name="home"),
    path("create_keyspace/", views.create_keyspace, name="create_keyspace"),
    path("create_default_groups/", views.create_default_groups, name="create_default_groups"),
    path("add_group/<str:grp_name>/", views.add_group, name="add_group"),
    path("add_group/", views.add_group, name="add_group"),
    path("rm_group/<str:grp_name>/", views.rm_group, name="rm_group"),
    path("create_default_users/", views.create_default_users, name="create_default_users"),
    path("add_user/<str:usr_name>/", views.add_user, name="add_user"),
    path("add_user/", views.add_user, name="add_user"),
    path("rm_user/<str:usr_name>/", views.rm_user, name="rm_user"),
]
