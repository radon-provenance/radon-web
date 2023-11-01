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

from . import views

app_name = "users"

urlpatterns = [
    path("", views.home, name="home"),
    path("login", views.userlogin, name="auth_login"),
    path("logout", views.userlogout, name="auth_logout"),
    path("new", views.new_user, name="new_user"),
    path("delete/<str:login>", views.delete_user, name="delete_user"),
    path("edit/<str:login>", views.edit_user, name="edit_user"),
    path("<str:login>", views.view, name="view"),
]
