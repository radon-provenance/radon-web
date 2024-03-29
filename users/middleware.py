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

from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin

from radon.model import User


class CassandraAuth(MiddlewareMixin):
    """Cassandra authentication , add the user in the cache request"""
 
    def process_request(self, request):
        """Process a request, add the user in the cache"""
 
        username = request.session.get("user")
        if not username:
            return None
 
        # Cache the user rather than hitting the database for
        # each request.  We can also invalidate the entry if the
        # user is marked as inactive.
        user = cache.get("user_{}".format(username), None)
        if not user:
            user = User.find(username)
        request.user = user
        cache.set("user_{}".format(username), user, 60)
 
        return None
