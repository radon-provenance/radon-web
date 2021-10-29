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
from django.conf.urls import include

from rest_framework.urlpatterns import format_suffix_patterns
from rest_cdmi.views import (
    CDMIView,
    capabilities,
    crud_id
)

app_name = "rest_cdmi"

urlpatterns = [
    path("cdmi_capabilities<path:path>", capabilities, name="capabilities"),
    # Find by uuid will require an improvement of the schema (TODO)
    # url(r'^cdmi_objectid/(?P<id>.*)$', crud_id, name='crud_id'),
    path("", CDMIView.as_view(), name="api_cdmi_root"),
    path("<path:path>", CDMIView.as_view(), name="api_cdmi"),
    #    url(r'^api-auth/', include('rest_framework.urls'))
]

urlpatterns = format_suffix_patterns(urlpatterns)
