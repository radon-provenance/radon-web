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

from django.contrib import admin
from django.urls import path

from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
# 
from project.views import home

urlpatterns = [
    path("favicon.ico", RedirectView.as_view(url="/static/img/favicon.ico")),
    path("", home, name="home"),
    path("activity/", include("activity.urls", namespace="activity")),
    path("archive/", include("archive.urls", namespace="archive")),
    path("groups/", include("groups.urls", namespace="groups")),
    path("users/", include("users.urls", namespace="users")),
    path("about/", TemplateView.as_view(template_name="about.html"), name="about"),
    path("contact/", TemplateView.as_view(template_name="contact.html"), name="contact"),
    path("settings/", include("settings.urls", namespace="settings")),
    path("api/cdmi/", include("rest_cdmi.urls", namespace="rest_cdmi")),
    path("api/admin/", include("rest_admin.urls", namespace="rest_admin")),
    path("msi/", include("msi.urls", namespace="msi")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

