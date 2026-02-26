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

import os
from django.apps import AppConfig
from django.conf import settings

from radon.model.collection import Collection
from radon.model.notification import test_mqtt_connection
from radon.model.user import User
from radon.database import (
    connect,
    check_keyspace,
    check_tables
)



def check_dse():
    settings.DSE_CONNECT = False
    settings.DSE_KEYSPACE = False
    settings.DSE_POPULATED = False
    
    try:
        connect_dse = connect(num_retries = 1)
        settings.DSE_CONNECT = connect_dse
    except Exception:
        settings.DSE_CONNECT = False
        return
    if not settings.DSE_CONNECT:
        return
    
    settings.DSE_KEYSPACE = check_keyspace() and check_tables()
    
    if not settings.DSE_KEYSPACE:
        return

    # At least 1 user has been created    
    users = User.objects.all()
    settings.DSE_POPULATED = len(users) != 0


def check_mqtt():
    settings.MQTT_CONNECT = False
    try:
        connect_mqtt = test_mqtt_connection()
        settings.MQTT_CONNECT = connect_mqtt
        return connect_mqtt
    except Exception:
        settings.MQTT_CONNECT = False
    return False




class RadonAppConfig(AppConfig):
    """The Radon application. We need to initialise Cassandra connection when
    the server is started"""

    name = "project"
    verbose_name = "Radon"
    

    def ready(self):
        # Django starts two processes with `python manage.py runserver`, we do
        # not want this initialisation to happen twice
        if os.environ.get('RUN_MAIN'):
            check_dse()
            check_mqtt()
            
            print(settings.DSE_CONNECT, settings.DSE_KEYSPACE, settings.DSE_POPULATED)
            print(settings.MQTT_CONNECT)

            print("allowed hosts: ", settings.ALLOWED_HOSTS)
            print("debug: ", settings.DEBUG)
            print("secret_key: ", settings.SECRET_KEY)
            
            
            
            # if settings.DSE_CONNECT:
            #     settings.DSE_OK = db_check()
            #     # If DSE_OK is False we need to do something, there's an error
            #     # with DSE initialisation
            # else:
            #     # If DSE_CONNECT is False we may need to do something
            #     # If we do nothing the web UI will display the connection
            #     # dialog box to specify the IP address for DSE and MQTT
            #     pass



