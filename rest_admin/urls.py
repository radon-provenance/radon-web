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

from django.conf.urls import (
    url,
    include
)
from rest_framework.urlpatterns import format_suffix_patterns


from rest_admin.views import (
    authenticate,
    group,
    groups,
    home,
    user,
    users
)

app_name = "rest_admin"

urlpatterns = [
   url(r'^authenticate$', authenticate),
   url(r'^users/(?P<username>.*)', user),
   url(r'^users', users),
   url(r'^groups/(?P<groupname>.*)', group),
   url(r'^groups', groups),
   url(r'^$', home),
   
]


urlpatterns = format_suffix_patterns(urlpatterns)
