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


import ldap

from django.conf import settings
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from rest_framework.authentication import (
    BasicAuthentication,
    exceptions
)

from radon.model.user import User


class CassandraMiddleware(MiddlewareMixin):
    """Cassandra authentication , add the user in the cache request"""
 
    def process_request(self, request):
        """Process a request, add the user in the cache"""
 
        username = request.session.get("user")
        if not username:
            return None
        
        user = cache.get("user_{}".format(username), None)
        if not user:
            user = User.find(username)
        request.user = user
        cache.set("user_{}".format(username), user, 60)
 
        return None



def ldap_authenticate(username, password):
    """Try to authenticate to a ldap server"""
    if settings.AUTH_LDAP_SERVER_URI is None:
        return False

    if settings.AUTH_LDAP_USER_DN_TEMPLATE is None:
        return False

    try:
        connection = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
        connection.protocol_version = ldap.VERSION3
        user_dn = settings.AUTH_LDAP_USER_DN_TEMPLATE % {"user": username}
        connection.simple_bind_s(user_dn, password)
        return True
    except ldap.INVALID_CREDENTIALS:
        return False
    except ldap.SERVER_DOWN:
        return False



class CassandraAuthentication(BasicAuthentication):
    """HTTP Basic authentication against username/password, stored in Cassandra"""

    www_authenticate_realm = "Radon"


    def authenticate_credentials(self, userid, password, request=None):
        """
        Authenticate the userid and password against username and password.
        """
        cass_user = User.find(userid)
        if cass_user is None or not cass_user.is_active():
            raise exceptions.AuthenticationFailed("User inactive or deleted.")
        if not cass_user.authenticate(password) and not ldap_authenticate(
            cass_user.uuid, password
        ):
            raise exceptions.AuthenticationFailed("Invalid username/password.")
        return (cass_user, None)
    