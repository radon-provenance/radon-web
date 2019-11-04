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

from django.apps import AppConfig

from radon.models import Collection, initialise


class RadonAppConfig(AppConfig):
    """The Radon application. We need to initialise Cassandra connection when
    the server is started"""

    name = "project"
    verbose_name = "Radon"

    def ready(self):
        initialise()

        # Try to get the root. It will be created if it doesn't exist
        Collection.get_root()
