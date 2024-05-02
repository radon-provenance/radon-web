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

from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns


from rest_admin.views import authenticate, group, groups, user, users

app_name = "rest_admin"

urlpatterns = [
    path("authenticate", authenticate),
    path("users/<str:username>", user),
    path("users", users),
    path("groups/<str:groupname>", group),
    path("groups", groups),
#    path("", home),
]


urlpatterns = format_suffix_patterns(urlpatterns)
