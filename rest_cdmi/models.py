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

import mimetypes

from radon.model.collection import Collection


class CDMIContainer():
    """Wrapper to return CDMI fields from a Collection"""

    def __init__(self, radon_container, api_root):
        self.collection = radon_container
        self.api_root = api_root

    def get_capabilitiesURI(self):
        """Mandatory URI to the capabilities for the object"""
        return "{0}/cdmi_capabilities/container{1}" "".format(
            self.api_root, self.collection.path
        )

    def get_children(self, child_range=None):
        """Mandatory - Names of the children objects in the container object."""
        child_c, child_r = self.collection.get_child()
        child_c = ["{}".format(c) for c in child_c]
        res = child_c + child_r
        if child_range:
            start, stop = (int(el) for el in child_range.split("-", 1))
            # map CDMI range value to python index
            stop += 1
        else:
            start = 0
            stop = len(res)
        return res[start:stop]

    def get_childrenrange(self):
        """Mandatory - The children of the container expressed as a range"""
        child_container, child_dataobject = self.collection.get_child()
        nb_child = len(child_container) + len(child_dataobject)
        if nb_child != 0:
            return "{}-{}".format(0, nb_child - 1)
        else:
            return "0-0"


    def get_completionStatus(self):
        """Mandatory - A string indicating if the object is still in the
        process of being created or updated by another operation,"""
        val = self.collection.get_cdmi_sys_meta().get("cdmi_completionStatus",
                                                      "Complete")
        return val


    def get_domainURI(self):
        """Mandatory URI of the owning domain"""
        return "{0}/cdmi_domains/radon/".format(self.api_root)


    def get_metadata(self):
        """Return metadata"""
        md = self.collection.get_cdmi_user_meta()
        md.update(self.collection.get_acl_metadata())
        return md


    def get_objectID(self):
        """Mandatory object ID of the object"""
        return self.collection.uuid

    def get_objectName(self):
        """Conditional name of the object
        We don't support objects only accessible by ID so this is mandatory"""
        return self.collection.name

    def get_objectType(self):
        """Mandatory Object type"""
        return "application/cdmi-container"

    def get_parentID(self):
        """Conditional Object ID of the parent container object
        We don't support objects only accessible by ID so this is mandatory"""
        parent_path = self.collection.container
        if self.collection.is_root:
            parent_path = "/"
        parent = Collection.find(parent_path)
        return parent.uuid

    def get_parentURI(self):
        """Conditional URI for the parent object
        We don't support objects only accessible by ID so this is mandatory"""
        # A container in CDMI has a '/' at the end but we don't (except for the
        # root)
        parent_path = self.collection.container
        if parent_path not in ('/', 'null'):
            parent_path = "{}".format(parent_path)
        return "{}".format(parent_path)

    def get_path(self):
        """Return collection path"""
        return self.collection.path

    def get_percentComplete(self):
        """Optional - Indicate the percentage of completion as a numeric
        integer value from 0 through 100. 100 if the completionStatus is
        'Complete'"""
        val = self.collection.get_cdmi_sys_meta().get("cdmi_percentComplete",
                                                      "100")
        return val


class CDMIResource():
    """Wrapper to return CDMI fields from a Resource"""

    def __init__(self, radon_resource, api_root):
        self.resource = radon_resource
        self.api_root = api_root

    def chunk_content(self):
        """Return a chunk of the resource"""
        return self.resource.chunk_content()

    def get_capabilitiesURI(self):
        """Mandatory URI to the capabilities for the object"""
        return "{0}/cdmi_capabilities/dataobject{1}" "".format(
            self.api_root, self.resource.path
        )

    def get_completionStatus(self):
        """Mandatory - A string indicating if the object is still in the
        process of being created or updated by another operation,"""
        val = self.resource.get_cdmi_sys_meta().get("cdmi_completionStatus",
                                                      "Complete")
        return val

    def get_domainURI(self):
        """Mandatory URI of the owning domain"""
        return "{0}/cdmi_domains/radon/".format(self.api_root)

    def get_length(self):
        """Return size of the resource"""
        return self.resource.get_size()

    def get_metadata(self):
        """Return metadata of the resource"""
        md = self.resource.get_cdmi_user_meta()
        md.update(self.resource.get_acl_metadata())
        return md

    def get_mimetype(self):
        """Return mimetype of the resource"""
        if self.resource.get_mimetype():
            return self.resource.get_mimetype()
        # Give best guess at mimetype
        mimetype = mimetypes.guess_type(self.resource.name)
        if mimetype[0]:
            return mimetype[0]
        else:
            # Interpret as binary data
            return "application/octet-stream"

    def get_objectID(self):
        """Mandatory object ID of the object"""
        return self.resource.uuid

    def get_objectName(self):
        """Conditional name of the object
        We don't support objects only accessible by ID so this is mandatory"""
        return self.resource.get_name()

    def get_objectType(self):
        """Mandatory Object type"""
        return "application/cdmi-object"

    def get_parentID(self):
        """Conditional Object ID of the parent container object
        We don't support objects only accessible by ID so this is mandatory"""
        parent = Collection.find(self.resource.container)
        return parent.uuid

    def get_parentURI(self):
        """Conditional URI for the parent object
        We don't support objects only accessible by ID so this is mandatory"""
        # A container in CDMI has a '/' at the end but we don't (except for the
        # root)
        parent_path = self.resource.container
        if parent_path != "/":
            parent_path = "{}".format(parent_path)
        return "{}".format(parent_path)

    def get_path(self):
        """Return resource path"""
        return self.resource.path

    def get_percentComplete(self):
        """Optional - Indicate the percentage of completion as a numeric
        integer value from 0 through 100. 100 if the completionStatus is
        'Complete'"""
        val = self.resource.get_cdmi_sys_meta().get("cdmi_percentComplete",
                                                      "100")
        return val

    def get_reference(self):
        """Return url of the resource"""
        return self.resource.url

    def get_url(self):
        """Return url of the resource"""
        return self.resource.url

    def get_value(self, child_range=None):
        """Return content of the resource"""
        data = []
        for chk in self.chunk_content():
            data.append(chk)
        res = b"".join([s for s in data])
        if child_range:
            start, stop = (int(el) for el in child_range.split("-", 1))
            # map CDMI range value to python index
            stop += 1
        else:
            start = 0
            stop = len(res)
        return str(res[start:stop])

    def get_valueRange(self):
        """Mandatory - The range of bytes of the data object to be returned in
        the value field"""
        return "0-{}".format(self.resource.get_size() - 1)

    def get_valueTransferEncoding(self):
        """Mandatory - The value transfer encoding used for the data object
        value"""
        return "utf-8"

    def is_reference(self):
        """Check if the resource is a reference"""
        return self.resource.is_reference()
