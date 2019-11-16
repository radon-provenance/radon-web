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

from rest_cdmi.capabilities import (
    StorageSystemMetadataCapabilities,
    ContainerCapabilities,
    DataObjectCapabilities,
)


class CDMIDataAccessObject():
    """CDMI Data Access Object to interact with a data store.

    Enhances the Abstract Base Data Access Object, providing CDMI capabilities
    and CDMI compliant identifier manipulation.
    """

    def __init__(self):
        self.metdata_capabilities = StorageSystemMetadataCapabilities(
            cdmi_acl=False,
            cdmi_size=False,
            cdmi_ctime=False,
            cdmi_atime=False,
            cdmi_mtime=False,
            cdmi_acount=False,
            cdmi_mcount=False,
        )
        self.container_capabilities = ContainerCapabilities(
            cdmi_create_container=False,
            cdmi_delete_container=False,
            cdmi_create_queue=False,
            cdmi_copy_queue=False,
            cdmi_move_queue=False,
            cdmi_read_metadata=False,
            cdmi_modify_metadata=False,
            cdmi_list_children=False,
            cdmi_list_children_range=False,
            cdmi_create_dataobject=False,
            cdmi_post_dataobject=False,
            cdmi_create_reference=False,
            cdmi_copy_dataobject=False,
            cdmi_move_dataobject=False,
        )
        self.data_object_capabilities = DataObjectCapabilities(
            cdmi_read_metadata=False,
            cdmi_read_value=False,
            cdmi_read_value_range=False,
            cdmi_modify_metadata=False,
            cdmi_modify_value=False,
            cdmi_delete_dataobject=False,
        )
