# Copyright 2023
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


import json
from django.shortcuts import render

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_405_METHOD_NOT_ALLOWED
)


from project.custom import CassandraAuthentication

from .models import MICROSERVICES



@authentication_classes((CassandraAuthentication,))
@permission_classes((IsAuthenticated,))
@api_view(["GET", "POST"])
def microservice(request, name):
    """REST calls for a microservice"""
    
    msi_def = MICROSERVICES.get(name, None)
    
    if request.method == "GET":
        return Response(msi_def.get("definition"), status=HTTP_200_OK)
    
    if request.method == "POST":
        try:
            body = request.body
            params_json = json.loads(body or '{}')
        except (TypeError, json.JSONDecodeError):
            return Response("Invalid JSON body", status=HTTP_400_BAD_REQUEST)

        try:
            output = msi_def.get("code")(params_json)
            return Response(output, status=HTTP_200_OK)
        except Exception as e:
            msg = "{}: {}".format(request.get_full_path(), str(e))
            return Response(msg, status=HTTP_400_BAD_REQUEST)

    else:
        return Response("Method Not Allowed", status=HTTP_405_METHOD_NOT_ALLOWED)










