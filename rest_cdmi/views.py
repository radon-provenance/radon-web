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

from collections import OrderedDict
import base64
import json
import logging
import time
import ldap

from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_204_NO_CONTENT,
    HTTP_206_PARTIAL_CONTENT,
    HTTP_302_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_406_NOT_ACCEPTABLE,
    HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
    HTTP_409_CONFLICT,
)
from rest_framework.renderers import BaseRenderer, JSONRenderer
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import BasicAuthentication, exceptions

from rest_framework.permissions import IsAuthenticated

from rest_cdmi.capabilities import SYSTEM_CAPABILITIES
from rest_cdmi.storage import CDMIDataAccessObject
from rest_cdmi.models import CDMIContainer, CDMIResource
from radon.model.collection import Collection
from radon.model.data_object import DataObject
from radon.model.resource import Resource
from radon.model.user import User
from radon.model.config import cfg
from radon.util import (
    merge,
    mk_cassandra_url,
    path_exists,
    split
) 
from radon.model.errors import ResourceConflictError
from project.custom import CassandraAuthentication
from radon.model.notification import (
    create_collection_request,
    create_resource_request,
    delete_collection_request,
    delete_resource_request,
    update_collection_request,
    update_resource_request,
    wait_response,
)
from radon.model.payload import (
    PayloadCreateCollectionRequest,
    PayloadCreateResourceRequest,
    PayloadDeleteCollectionRequest,
    PayloadDeleteResourceRequest,
    PayloadUpdateCollectionRequest,
    PayloadUpdateResourceRequest,
)


CHUNK_SIZE = 1048576

# List of supported version (In order so the first to be picked up is the most
# recent one
CDMI_SUPPORTED_VERSION = ["1.1", "1.1.1", "1.0.2"]

# Possible sections of the CDMI request body where the data object content
# may be specified
POSSIBLE_DATA_OBJECT_LOCATIONS = [
    "deserialize",
    "serialize",
    "copy",
    "move",
    "reference",
    "deserializevalue",
    "value",
]

# Body fields for reading a data object object using CDMI, the value of the
# dictionary can be used to pass parameters
FIELDS_DATA_OBJECT = OrderedDict(
    [
        ("objectType", None),
        ("objectID", None),
        ("objectName", None),
        ("parentURI", None),
        ("parentID", None),
        ("domainURI", None),
        ("capabilitiesURI", None),
        ("completionStatus", None),
        ("percentComplete", None),
        ("mimetype", None),
        ("metadata", None),
        ("valueTransferEncoding", None),
        ("value", None),
        ("valueRange", None),
    ]
)

FIELDS_REFERENCE = OrderedDict(
    [
        ("objectType", None),
        ("objectID", None),
        ("objectName", None),
        ("parentURI", None),
        ("parentID", None),
        ("domainURI", None),
        ("capabilitiesURI", None),
        ("metadata", None),
        ("reference", None),
    ]
)

# Body fields for reading a container object using CDMI, the value of the
# dictionary can be used to pass parameters
FIELDS_CONTAINER = OrderedDict(
    [
        ("objectType", None),
        ("objectID", None),
        ("objectName", None),
        ("parentURI", None),
        ("parentID", None),
        ("domainURI", None),
        ("capabilitiesURI", None),
        ("completionStatus", None),
        ("percentComplete", None),
        ("metadata", None),
        ("childrenrange", None),
        ("children", None),
    ]
)


MSG_UNSUPPORTED_VERSION = "Unsupported CDMI version"

APP_CDMI_CAPABILITY = "application/cdmi-capability"
APP_CDMI_CONTAINER = "application/cdmi-container"
APP_CDMI_OBJECT = "application/cdmi-object"


class CDMIContainerRenderer(JSONRenderer):
    """
    Renderer which serializes CDMI container to JSON.
    """

    media_type = "application/cdmi-container;application/cdmi-container+json"
    format = "cdmic"
    charset = "utf-8"


class CDMIObjectRenderer(JSONRenderer):
    """
    Renderer which serializes CDMI data object to JSON.
    """

    media_type = "application/cdmi-object; application/cdmi-object+json"
    format = "cdmi"
    charset = "utf-8"


class OctetStreamRenderer(BaseRenderer):
    """
    Renderer which serializes CDMI data object to binary
    """

    media_type = "application/octet-stream"
    format = "bin"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class CDMIView(APIView):
    """Class that manages cdmi requests"""

    authentication_classes = (CassandraAuthentication,)
    renderer_classes = (
        CDMIContainerRenderer,
        CDMIObjectRenderer,
        JSONRenderer,
        OctetStreamRenderer,
    )
    permission_classes = (IsAuthenticated,)

    def __init__(self, **kwargs):
        super(CDMIView, self).__init__(**kwargs)
        cfg = settings.CDMI_SERVER
        self.api_root = cfg["endpoint"]
        self.logger = logging.getLogger("radon")
        self.http_mode = True
        self.cdmi_version = "HTTP"
        self.user = None

    def check_cdmi_version(self):
        """Check the HTTP request header to see what version the client is
        supporting. Return the highest version supported by both the client and
        the server,
        '' if no match is found or no version provided by the client
        'HTTP' if the cdmi header is not present"""
        return check_cdmi_version(self.request)


    def create_resource(self, request, path, mimetype, content=None, metadata=None,
                        url=None):
        """Create a new resource in http mode"""
        parent, name = split(path)
        
        payload_json = {
            "obj": {
                "name" : name,
                "container": parent,
                "path": path,
                "mimetype": mimetype,
            },
            "meta": {
                "sender": request.user.login,
            }
        }
        if metadata:
            payload_json["obj"]["metadata"] = metadata
        if url: # reference
            payload_json["obj"]["url"] = url
        
        notif = create_resource_request(PayloadCreateResourceRequest(payload_json))
        resp = wait_response(notif.req_id)

        status = HTTP_400_BAD_REQUEST
        resource = None
        if resp == 0:
            resource = Resource.find(path)
            if content:
                resource.put(content)
            status = HTTP_201_CREATED
        elif resp == 2:
            status = HTTP_202_ACCEPTED
        return(status, resource)


    @csrf_exempt
    def delete(self, request, path=u"/"):
        """Delete request on a container or a resource path"""
        self.user = request.user
        # Check HTTP Headers for CDMI version or HTTP mode
        self.cdmi_version = self.check_cdmi_version()
        if not self.cdmi_version:
            self.logger.warning(MSG_UNSUPPORTED_VERSION)
            return Response(status=HTTP_400_BAD_REQUEST)
        self.http_mode = self.cdmi_version == "HTTP"
        # Add a '/' at the beginning if not present
        if not path.startswith("/"):
            path = u"/{}".format(path)
        # In CDMI standard a container is defined by the / at the end
        is_container = path.endswith("/")
        if not path or path == "/":
            # Refuse to delete root container
            return Response(status=HTTP_409_CONFLICT)
        elif is_container:
            # Delete container
            return self.delete_container(request, path)
        else:
            # Delete data object
            return self.delete_data_object(request, path)


    def delete_container(self, request, path):
        """Delete a container"""
        collection = Collection.find(path)
        if not collection:
            self.logger.info(u"Fail to delete collection at '{}'".format(path))
            return Response(status=HTTP_404_NOT_FOUND)
        if not collection.user_can(self.user, "delete"):
            self.logger.warning(
                u"User {} tried to delete container '{}'".format(self.user, path)
            )
            return Response(status=HTTP_403_FORBIDDEN)
        
        
        notif = delete_collection_request(PayloadDeleteCollectionRequest.default(path, request.user.login))
        resp = wait_response(notif.req_id)

        if resp == 0:
            msg = "Collection '{}' has been deleted".format(path)
            status_code = HTTP_204_NO_CONTENT
        elif resp == 1:
            msg = "Deletion of collection '{}' has failed".format(path)
            status_code = HTTP_400_BAD_REQUEST
        else:
            msg = "Deletion of collection '{}' is still pending".format(path)
            status_code = HTTP_202_ACCEPTED
        
        self.logger.info(msg)
        return Response(status=status_code)


    def delete_data_object(self, request, path):
        """Delete a resource"""
        resource = Resource.find(path)
        if not resource:
            collection = Collection.find(path)
            if collection:
                self.logger.info(
                    u"Fail to delete resource at '{}', test if it's a collection".format(
                        path
                    )
                )
                return self.delete_container(request, path)
            else:
                self.logger.info(u"Fail to delete resource at '{}'".format(path))
                return Response(status=HTTP_404_NOT_FOUND)
        if not resource.user_can(self.user, "delete"):
            self.logger.warning(
                u"User {} tried to delete resource '{}'".format(self.user, path)
            )
            return Response(status=HTTP_403_FORBIDDEN)

        resource.delete()
        self.logger.info(u"The resource '{}' was successfully deleted".format(path))
        return Response(status=HTTP_204_NO_CONTENT)


    @csrf_exempt
    def get(self, request, path="/"):
        """Get request on a container or a resource path"""
        self.user = request.user
        # Check HTTP Headers for CDMI version or HTTP mode
        self.cdmi_version = self.check_cdmi_version()
        if not self.cdmi_version:
            self.logger.warning(MSG_UNSUPPORTED_VERSION)
            return Response(status=HTTP_400_BAD_REQUEST)
        self.http_mode = self.cdmi_version == "HTTP"

        # Add a '/' at the beginning if not present
        if not path.startswith("/"):
            path = "/{}".format(path)
        # In CDMI standard a container is defined by the / at the end
        is_container = path.endswith("/")
        if is_container:
            return self.read_container(path)
        else:
            return self.read_data_object(path)


    @csrf_exempt
    def put(self, request, path="/"):
        """Put request on a container or a resource path"""
        self.user = request.user
        # Check HTTP Headers for CDMI version or HTTP mode
        self.cdmi_version = self.check_cdmi_version()
        if not self.cdmi_version:
            self.logger.warning(MSG_UNSUPPORTED_VERSION)
            return Response(status=HTTP_400_BAD_REQUEST)
        self.http_mode = self.cdmi_version == "HTTP"

        # Add a '/' at the beginning if not present
        if not path.startswith("/"):
            path = "/{}".format(path)
        # In CDMI standard a container is defined by the / at the end
        is_container = path.endswith("/")
        if is_container:
            return self.put_container(request, path)
        else:
            return self.put_resource(request, path)


    def put_container(self, request, path):
        """Create a new container"""
        try:
            body = self.request.body
            request_body = json.loads(body)
        except (TypeError, json.JSONDecodeError):
            request_body = {}
        
        # Check if the container already exists
        collection = Collection.find(path)
        
        # Update Collection
        if collection:
            if not collection.user_can(self.user, "edit"):
                self.logger.warning(
                    "User {} tried to modify collection at '{}'".format(
                        self.user, path
                    )
                )
                return Response(status=HTTP_403_FORBIDDEN)
            if self.http_mode:
                # HTTP Request, unsupported
                self.logger.warning(
                    "Update collection '{}' using HTTP is undefined".format(path)
                )
                return Response("Update collection using HTTP is undefined", 
                                status=HTTP_406_NOT_ACCEPTABLE)
            return self.update_container(request, request_body, collection)

        # Create Collection
        parent, name = split(path)
        if name.startswith("cdmi_"):
            return Response(
                "cdmi_ prefix is not a valid name for a container",
                status=HTTP_400_BAD_REQUEST,
            )
        parent_collection = Collection.find(parent)
        if not parent_collection:
            self.logger.info(
                "Fail to create a collection at '{}', parent collection doesn't exist".format(
                    path
                )
            )
            return Response(status=HTTP_404_NOT_FOUND)
        # Check if user can create a new collection in the collection
        if not parent_collection.user_can(self.user, "write"):
            self.logger.warning(
                "User {} tried to create new collection at '{}'".format(
                    self.user, path
                )
            )
            return Response(status=HTTP_403_FORBIDDEN)

        obj = { 
            "name" : name,
            "container": parent,
            "path": path,
        }
        metadata = request_body.get("metadata", {})
        if metadata:
            obj["metadata"] = metadata
        
        payload_json = {
            "obj": obj,
            "meta": {"sender": request.user.login}
        }
        
        notif = create_collection_request(PayloadCreateCollectionRequest(payload_json))
        resp = wait_response(notif.req_id)
        
        if resp == 0:
            collection = Collection.find(path)
            cdmi_container = CDMIContainer(collection, self.api_root)
            
            if self.http_mode:
                return Response(status=HTTP_202_ACCEPTED)
            else:
                # CDMI mode
                body = OrderedDict()
                for field, value in FIELDS_CONTAINER.items():
                    get_field = getattr(cdmi_container, "get_{}".format(field))
                    body[field] = get_field()
    
                response_status = HTTP_201_CREATED
                body["completionStatus"] = "Complete"
                return JsonResponse(
                    body, content_type=body["objectType"], status=response_status
                )
        elif resp == 1:
            return Response(status=HTTP_400_BAD_REQUEST)
        else: # Still pending
            if self.http_mode:
                # Specification states that:
                #
                #     A response message body may be provided as per RFC 2616.
                #
                # Send the CDMI response but with Content-Type = application/json
                #content_type = "application/json"
                # Mandatory completionStatus
                # Does not accept CDMI - cannot return "202 Accepted"
                return Response(status=HTTP_201_CREATED)
            else:
                body = {
                    "objectType" :"application/cdmi-container",
                    "completionStatus" : "Processing"
                }
                return JsonResponse(
                    body, content_type=body["objectType"], status=HTTP_202_ACCEPTED
                )


    def put_resource(self, request, path):
        """Put a data object to a specific collection"""
        # Check if a collection with the name exists
        collection = Collection.find(path)
        if collection:
            # Try to put a data_object when a collection of the same name
            # already exists
            self.logger.info(
                "Impossible to create a new resource, the collection '{}' already exists, try to update it".format(
                    path
                )
            )
            return self.put_container(request, path)
        
        if self.http_mode:
            return self.put_resource_http(request, path)
        else:
            return self.put_resource_cdmi(request, path)


    def put_resource_cdmi(self, request, path):
        parent, name = split(path)
        sys_meta = {}
        # Check if the resource already exists
        resource = Resource.find(path)
        url = None

        tmp = self.request.content_type.split("; ")
        content_type = tmp[0]
        if not content_type:
            # This is mandatory - either application/cdmi-object or
            # mimetype of data object to create
            return Response(status=HTTP_400_BAD_REQUEST)
        if content_type == APP_CDMI_CONTAINER:
            # CDMI request performed to create a new container resource
            # but omitting the trailing slash at the end of the URI
            # CDMI standards mandates 400 Bad Request response
            return Response(status=HTTP_400_BAD_REQUEST)

        try:
            body = self.request.body
            request_body = json.loads(body)
        except (json.JSONDecodeError, TypeError):
            return Response(status=HTTP_400_BAD_REQUEST)
        value_type = [
            key for key in request_body if key in POSSIBLE_DATA_OBJECT_LOCATIONS
        ]
        if not value_type and not resource:
            # We need a value to create a resource
            return Response(status=HTTP_400_BAD_REQUEST)
        if len(value_type) > 1:
            # Only one of these fields shall be specified in any given
            # operation.
            return Response(status=HTTP_400_BAD_REQUEST)
        elif value_type and (value_type[0] not in ["value", "reference"]):
            # Only 'value' and 'reference' are supported at the present time
            # TODO: Check the authorized fields with reference
            return Response(status=HTTP_400_BAD_REQUEST)

        is_reference = False  # By default
        # CDMI specification mandates that text/plain should be used
        # where mimetype is absent
        mimetype = request_body.get("mimetype", "text/plain")
        if value_type:
            if value_type[0] == "value":
                content = request_body.get(value_type[0]).encode()
                encoding = request_body.get("valuetransferencoding", "utf-8")
                if encoding == "base64":
                    try:
                        content = base64.b64decode(content)
                    except TypeError:
                        return Response(status=HTTP_400_BAD_REQUEST)
                elif encoding != "utf-8":
                    return Response(status=HTTP_400_BAD_REQUEST)
                sys_meta["cdmi_valuetransferencoding"] = encoding
            elif value_type[0] == "reference":
                is_reference = True
                if resource:
                    # References cannot be updated so we can't create a new one
                    return Response(status=HTTP_409_CONFLICT)
                url = request_body.get(value_type[0])

         # Assemble metadata
        metadata = request_body.get("metadata", {})
        
        # Check permissions
        if resource:
            # Update Resource, check we can edit it
            if not resource.user_can(self.user, "edit"):
                self.logger.warning(
                    "User {} tried to modify resource at '{}'".format(self.user, path)
                )
                return Response(status=HTTP_403_FORBIDDEN)
        
            status, resource = self.update_resource(request, resource, mimetype, 
                                                   content, metadata, url)
        else:
            # Create Resource
            parent_collection = Collection.find(parent)
            if not parent_collection:
                self.logger.info(
                    "Fail to create a resource at '{}', collection doesn't exist".format(
                        path
                    )
                )
                return Response(status=HTTP_404_NOT_FOUND)
            # Check if user can create a new resource in the collection
            if not parent_collection.user_can(self.user, "write"):
                self.logger.warning(
                    "User {} tried to create new resource at '{}'".format(
                        self.user, path
                    )
                )
                return Response(status=HTTP_403_FORBIDDEN)

            status, resource = self.create_resource(request, path, mimetype, 
                        content, metadata, url)
        
        if not resource:
            return Response(status=status)
        
        cdmi_resource = CDMIResource(resource, self.api_root)

        if cdmi_resource.is_reference():
            field_dict = FIELDS_REFERENCE
        else:
            field_dict = FIELDS_DATA_OBJECT

        body = OrderedDict()
        for field, value in field_dict.items():
            get_field = getattr(cdmi_resource, "get_{}".format(field))
            # If we ask the value with a range value we need to update the
            # valuerange value
            # The valuerange should be created before the value field
            if field == "value" and value and "valuerange" in body:
                body["valuerange"] = value
            try:
                if field in ["value", "valuerange"] and is_reference:
                    continue
                body[field] = get_field()
            except AttributeError:
                self.logger.error(
                    "Parameter problem for resource '{}' ('{}={}')".format(
                        cdmi_resource.get_path(), field, value
                    )
                )
                return Response(status=HTTP_406_NOT_ACCEPTABLE)

        return JsonResponse(
            body, content_type=APP_CDMI_OBJECT, status=HTTP_201_CREATED
        )
            


    def put_resource_http(self, request, path):
        parent, name = split(path)

        tmp = self.request.content_type.split("; ")
        content_type = tmp[0]
        if not content_type:
            mimetype = "application/octet-stream"
        elif content_type == APP_CDMI_OBJECT:
            # Should send the X-CDMI-Specification-Version to use this
            # mimetype
            return Response(status=HTTP_400_BAD_REQUEST)
        else:
            mimetype = content_type
        content = self.request.body

        # Check if the resource already exists
        resource = Resource.find(path)

        if resource:
            # Update Resource
            # Check permissions
            if not resource.user_can(self.user, "edit"):
                self.logger.warning(
                    "User {} tried to modify resource at '{}'".format(self.user, path)
                )
                return Response(status=HTTP_403_FORBIDDEN)
            status, resource = self.update_resource(request, resource, mimetype, content)
            return Response(status=status)

        else:
            # Create Resource
            # Check permissions
            parent_collection = Collection.find(parent)
            if not parent_collection:
                self.logger.info(
                    "Fail to create a resource at '{}', collection doesn't exist".format(
                        path
                    )
                )
                return Response(status=HTTP_404_NOT_FOUND)
            # Check if user can create a new resource in the collection
            if not parent_collection.user_can(self.user, "write"):
                self.logger.warning(
                    "User {} tried to create new resource at '{}'".format(
                        self.user, path
                    )
                )
                return Response(status=HTTP_403_FORBIDDEN)

            status, resource = self.create_resource(request, path, mimetype, content)
            return Response(status=status)


    def read_container(self, path):
        """Get information on a container"""
        collection = Collection.find(path)
        if not collection:
            self.logger.info(u"Fail to read a collection at '{}'".format(path))
            return Response(status=HTTP_404_NOT_FOUND)
        if not collection.user_can(self.user, "read"):
            self.logger.warning(
                u"User {} tried to read container at '{}'".format(self.user, path)
            )
            return Response(status=HTTP_403_FORBIDDEN)

        cdmi_container = CDMIContainer(collection, self.api_root)
        if self.http_mode:
            # HTTP Request, unsupported
            self.logger.warning(
                u"Read container '{}' using HTTP is undefined".format(path)
            )
            return Response(status=HTTP_406_NOT_ACCEPTABLE)
        else:
            # Read using CDMI
            return self.read_container_cdmi(cdmi_container)


    def read_container_cdmi(self, cdmi_container):
        """Get container information, cdmi mode"""
        path = cdmi_container.get_path()
        http_accepts = self.request.META.get("HTTP_ACCEPT", "").split(",")
        http_accepts = {el.split(";")[0] for el in http_accepts}
        if not http_accepts.intersection(set([APP_CDMI_CONTAINER, "*/*"])):
            self.logger.error(
                u"Accept header problem for container '{}' ('{}')".format(
                    path, http_accepts
                )
            )
            return Response(status=HTTP_406_NOT_ACCEPTABLE)
        if self.request.GET:
            fields = {}
            for field, value in self.request.GET.items():
                if field in FIELDS_CONTAINER:
                    fields[field] = value
                else:
                    self.logger.error(
                        u"Parameter problem for container '{}' ('{} undefined')".format(
                            path, field
                        )
                    )
                    return Response(status=HTTP_406_NOT_ACCEPTABLE)
        else:
            fields = FIELDS_CONTAINER

        # Obtained information in a dictionary
        body = OrderedDict()

        for field, value in fields.items():
            get_field = getattr(cdmi_container, "get_{}".format(field))
            # If we send children with a range value we need to update the
            # childrenrange value
            # The childrenrange should be created before the children field
            if field == "children" and value and "childrenrange" in body:
                body["childrenrange"] = value
            try:
                if value:
                    body[field] = get_field(value)
                else:
                    body[field] = get_field()
            except AttributeError:
                self.logger.error(
                    u"Parameter problem for container '{}' ('{}={}')".format(
                        path, field, value
                    )
                )
                return Response(status=HTTP_406_NOT_ACCEPTABLE)

        self.logger.info(
            u"{} reads container at '{}' using CDMI".format(self.user.login, path)
        )
        response = JsonResponse(body, content_type=APP_CDMI_CONTAINER)
        response["X-CDMI-Specification-Version"] = "1.1"
        return response


    def read_data_object(self, path):
        """Read a resource"""
        resource = Resource.find(path)
        if not resource:
            collection = Collection.find(path)
            if collection:
                self.logger.info(
                    u"Fail to read a resource at '{}', test if it's a collection".format(
                        path
                    )
                )
                return self.read_container(path)
            else:
                self.logger.info(u"Fail to read a resource at '{}'".format(path))
                return Response(status=HTTP_404_NOT_FOUND)
        if not resource.user_can(self.user, "read"):
            self.logger.warning(
                u"User {} tried to read resource at '{}'".format(self.user, path)
            )
            return Response(status=HTTP_403_FORBIDDEN)
        cdmi_resource = CDMIResource(resource, self.api_root)
        if self.http_mode:
            if cdmi_resource.is_reference():
                return self.read_data_object_reference(cdmi_resource)
            else:
                return self.read_data_object_http(cdmi_resource)
        else:
            return self.read_data_object_cdmi(cdmi_resource)


    def read_data_object_cdmi(self, cdmi_resource):
        """Read a resource, cdmi mode"""
        path = cdmi_resource.get_path()
        http_accepts = self.request.META.get("HTTP_ACCEPT", "").split(",")
        http_accepts = {el.split(";")[0] for el in http_accepts}
        if not http_accepts.intersection(set([APP_CDMI_OBJECT, "*/*"])):
            self.logger.error(
                u"Accept header problem for resource '{}' ('{}')".format(
                    path, http_accepts
                )
            )
            return Response(status=HTTP_406_NOT_ACCEPTABLE)

        if cdmi_resource.is_reference():
            field_dict = FIELDS_REFERENCE
            status = HTTP_302_FOUND
        else:
            field_dict = FIELDS_DATA_OBJECT
            if "value" in field_dict:
                del field_dict["value"]
            if "valuerange" in field_dict:
                del field_dict["valuerange"]
            status = HTTP_200_OK

        if self.request.GET:
            fields = {}
            for field, value in self.request.GET.items():
                if field in field_dict.keys():
                    fields[field] = value
                else:
                    self.logger.error(
                        u"Parameter problem for resource '{}' ('{} undefined')".format(
                            path, field
                        )
                    )
                    return Response(status=HTTP_406_NOT_ACCEPTABLE)
        else:
            fields = field_dict

        # Obtained information in a dictionary
        body = OrderedDict()
        for field, value in fields.items():
            get_field = getattr(cdmi_resource, "get_{}".format(field))
            # If we ask the value with a range value we need to update the
            # valuerange value
            # The valuerange should be created before the value field
            if field == "value" and value and "valuerange" in body:
                body["valuerange"] = value
            #             try:
            #                 if value:
            #                     body[field] = get_field(value)
            #                 else:
            #                     body[field] = get_field()
            #             except Exception as e:
            #                 self.logger.error("Parameter problem for resource '{}' ('{}={}')".format(path, field, value))
            #                 return Response(status=HTTP_406_NOT_ACCEPTABLE)
            if value:
                body[field] = get_field(value)
            else:
                body[field] = get_field()

        self.logger.info(
            u"{} reads resource at '{}' using CDMI".format(self.user.login, path)
        )
        response = JsonResponse(
            body, content_type=APP_CDMI_OBJECT, status=status
        )
        response["X-CDMI-Specification-Version"] = "1.1"
        return response


    def read_data_object_http(self, cdmi_resource):
        """Read a resource, http mode"""
        path = cdmi_resource.get_path()

        if "HTTP_RANGE" in self.request.META:
            # Use range header
            specifier = self.request.META.get("HTTP_RANGE", "")
            http_range = parse_range_header(specifier, cdmi_resource.get_length())
            if not http_range:
                self.logger.error(
                    u"Range header parsing failed '{}' for resource '{}'".format(
                        specifier, path
                    )
                )
                return Response(status=HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE)
            else:
                self.logger.info(
                    u"{} reads resource at '{}' using HTTP, with range '{}'".format(
                        self.user.login, path, http_range
                    )
                )
                # Totally inefficient but that's probably not something
                # we're gonna use a lot
                value = cdmi_resource.get_value()
                data = []
                for (start, stop) in http_range:
                    data.append(value[start:stop])
                data = "".join([d for d in data])
                status = HTTP_206_PARTIAL_CONTENT
            return StreamingHttpResponse(
                streaming_content=data,
                content_type=cdmi_resource.get_mimetype(),
                status=status,
            )
        else:
            self.logger.info(
                u"{} reads resource at '{}' using HTTP".format(self.user.login, path)
            )
            status = HTTP_200_OK
            return StreamingHttpResponse(
                streaming_content=cdmi_resource.chunk_content(),
                content_type=cdmi_resource.get_mimetype(),
                status=status,
            )


    def read_data_object_reference(self, cdmi_resource):
        """Read a resource, when it's a reference"""
        return Response(
            status=HTTP_302_FOUND, headers={"Location": cdmi_resource.get_url()}
        )


    def update_container(self, request, request_body, collection):
        """Modify a container"""
        metadata = request_body.get("metadata", {})
        if metadata:
            payload_json = {
                "obj": {
                    "name" : collection.name,
                    "container": collection.container,
                    "path": collection.path,
                    "metadata": metadata,
                },
                "meta": {
                    "sender": request.user.login,
                }
            }

            notif = update_collection_request(PayloadUpdateCollectionRequest(payload_json))
            resp = wait_response(notif.req_id)
            if resp == 0:
                return Response(status=HTTP_204_NO_CONTENT)
            elif resp == 1:
                return Response(status=HTTP_400_BAD_REQUEST)
            else:
                return Response(status=HTTP_202_ACCEPTED)
        else:
            # No metadata
            return Response(status=HTTP_409_CONFLICT)


    def update_resource(self, request, resource, mimetype, content, 
                             metadata=None, url=None):
        """Upload data object"""
        path = resource.path
        if resource:
            payload_json = {
                "obj": {
                    "name" : resource.name,
                    "container": resource.container,
                    "path": resource.path,
                    "mimetype": mimetype,
                },
                "meta": {
                    "sender": request.user.login,
                }
            }
            if metadata:
                payload_json["obj"]["metadata"] = metadata
            if url: # reference
                payload_json["obj"]["url"] = url
            notif = update_resource_request(PayloadUpdateResourceRequest(payload_json))
            resp = wait_response(notif.req_id)

            status =  HTTP_400_BAD_REQUEST
            resource = None
            if resp == 0:
                resource = Resource.find(path)
                if content:
                    resource.put(content)
                status = HTTP_201_CREATED
            elif resp == 2:
                status = HTTP_202_ACCEPTED
            return(status, resource)



def capabilities(request, path):
    """Read all fields from an existing capability object.

    TODO: This part of the specification isn't implemented properly according
    to the specification, capabilities should be a special kind of containers
    with ObjectID"""
    cdmi_version = check_cdmi_version(request)
    if not cdmi_version:
        return HttpResponse(status=HTTP_400_BAD_REQUEST)
    body = OrderedDict()
    if path in ["", "/"]:
        body["capabilities"] = SYSTEM_CAPABILITIES._asdict()
        body["objectType"] = APP_CDMI_CAPABILITY
        body["objectID"] = "00007E7F00104BE66AB53A9572F9F51E"
        body["objectName"] = "cdmi_capabilities/"
        body["parentURI"] = "/"
        body["parentID"] = "00007E7F0010128E42D87EE34F5A6560"
        body["childrenrange"] = "0-3"
        body["children"] = ["domain/", "container/", "data_object/", "queue/"]
    elif not path.endswith("/"):
        data_dict = CDMIDataAccessObject().data_object_capabilities._asdict()
        body["capabilities"] = data_dict
        body["objectType"] = APP_CDMI_CAPABILITY
        body["objectID"] = "00007E7F00104BE66AB53A9572F9F51F"
        body["objectName"] = "data_object/"
        body["parentURI"] = "/"
        body["parentID"] = "00007E7F00104BE66AB53A9572F9F51FE"
        body["childrenrange"] = "0"
        body["children"] = []
    else:
        data_dict = CDMIDataAccessObject().container_capabilities._asdict()
        body["capabilities"] = data_dict
        body["objectType"] = APP_CDMI_CAPABILITY
        body["objectID"] = "00007E7F00104BE66AB53A9572F9F51A"
        body["objectName"] = "container/"
        body["parentURI"] = "/"
        body["parentID"] = "00007E7F00104BE66AB53A9572F9F51E"
        body["childrenrange"] = "0"
        body["children"] = []
    return JsonResponse(body)


def check_cdmi_version(request):
    """Check the HTTP request header to see what version the client is
     supporting. Return the highest version supported by both the client and
     the server,
     '' if no match is found or no version provided by the client
     'HTTP' if the cdmi header is not present"""
    if "HTTP_X_CDMI_SPECIFICATION_VERSION" not in request.META:
        return "HTTP"
    spec_version_raw = request.META.get("HTTP_X_CDMI_SPECIFICATION_VERSION", "")
    versions_list = [el.strip() for el in spec_version_raw.split(",")]
    for version in CDMI_SUPPORTED_VERSION:
        if version in versions_list:
            return version
    return ""


def chunkstring(string, length):
    """"Return a chunk of a string"""
    return (string[0 + i : length + i] for i in range(0, len(string), length))



@api_view(["GET", "PUT"])
@authentication_classes(
    [CassandraAuthentication,]
)


def crud_id(request, obj_id):
    """Call the correct method from a call with the uuid of a resource/collection"""
    # The URL should end with a '/'
    obj_id = obj_id.replace("/", "")
    collection = Collection.find_by_uuid(obj_id)
    if collection:
        return redirect("rest_cdmi:api_cdmi", path=collection.path())
    else:
        resource = Resource.find_by_uuid(obj_id)
        if resource:
            return redirect("rest_cdmi:api_cdmi", path=resource.path())
        else:
            return Response(status=HTTP_404_NOT_FOUND)


def parse_range_header(specifier, len_content):
    """Parses a range header into a list of pairs (start, stop)"""
    if not specifier or "=" not in specifier:
        return []

    ranges = []
    unit, byte_set = specifier.split("=", 1)
    unit = unit.strip().lower()

    if unit != "bytes":
        return []

    for val in byte_set.split(","):
        val = val.strip()
        if "-" not in val:
            return []

        if val.startswith("-"):
            # suffix-byte-range-spec: this form specifies the last N
            # bytes of an entity-body
            start = len_content + int(val)
            if start < 0:
                start = 0
            stop = len_content
        else:
            # byte-range-spec: first-byte-pos "-" [last-byte-pos]
            start, stop = val.split("-", 1)
            start = int(start)
            # Add 1 to make stop exclusive (HTTP spec is inclusive)
            stop = int(stop) + 1 if stop else len_content
            if start >= stop:
                return []

        ranges.append((start, stop))

    return ranges



