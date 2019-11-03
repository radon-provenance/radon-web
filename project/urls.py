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

from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from project.views import home

urlpatterns = [
    url(r"^favicon\.ico$", RedirectView.as_view(url="/static/img/favicon.ico")),
    #    url(r'^admin/', admin.site.urls),
    url(r"^$", home, name="home"),
    url(r"^activity/", include("activity.urls", namespace="activity")),
    url(r"^archive/", include("archive.urls", namespace="archive")),
    url(r"^groups/", include("groups.urls", namespace="groups")),
    url(r"^users/", include("users.urls", namespace="users")),
    url(r"^about$", TemplateView.as_view(template_name="about.html"), name="about"),
    url(
        r"^contact$", TemplateView.as_view(template_name="contact.html"), name="contact"
    ),
    url(r"^api/cdmi/", include("rest_cdmi.urls", namespace="rest_cdmi")),
    url(r"^api/admin/", include("rest_admin.urls", namespace="rest_admin")),
]
