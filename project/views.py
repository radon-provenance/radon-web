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

from django.shortcuts import render, redirect
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from django.http import JsonResponse

from radon.model.config import cfg
from radon.model.notification import test_mqtt_connection
from radon.util import list_to_csv
from radon.database import initialise
from radon.util import csv_to_list

from .forms import ConnectionForm
from .apps import (
    check_dse,
    check_mqtt
)



def test_dse(request):
    status = "error"
    message = "Invalid Request"
    if request.method == 'POST':
        cfg.dse_host = csv_to_list(request.POST.get('db_host'))
        check_dse()
        if settings.DSE_CONNECT:
            status = "success"
            message = "Connection Ok"
        else:
            status = "error"
            message = "Connection failed"
    response_data = {'status': status, 'message': message}
    return JsonResponse(response_data)


def test_mqtt(request):
    status = "error"
    message = "Invalid Request"
    if request.method == 'POST':
        cfg.mqtt_host = request.POST.get('mqtt_host')
        check_mqtt()
        if settings.MQTT_CONNECT:
            status = "success"
            message = "Connection Ok"
        else:
            status = "error"
            message = "Connection failed"
    response_data = {'status': status, 'message': message}
    return JsonResponse(response_data)


def home(request):
    """Main view for the radon web interface"""
    check_dse()
    check_mqtt()
    print(settings.DSE_CONNECT, settings.DSE_KEYSPACE, settings.DSE_POPULATED)
    print(settings.MQTT_CONNECT)
    # Display connection modal window to setup DSE and MQTT hosts
    if not settings.DSE_CONNECT or not settings.MQTT_CONNECT:
        if request.method == 'POST':
            form = ConnectionForm(request.POST)
            if form.is_valid():
                cfg.dse_host = csv_to_list(form.cleaned_data["db_host"])
                check_dse()
                cfg.mqtt_host = form.cleaned_data["mqtt_host"]
                check_mqtt()
                # TODO: Store cfg.dse_host and cfg.mqtt_host somewhere
            
            return redirect("home")
        else:
            form = ConnectionForm(initial={"db_host" : list_to_csv(cfg.dse_host),
                                           "mqtt_host" : cfg.mqtt_host})
            return render(request, "index.html", {"dse_connect" : settings.DSE_CONNECT,
                                                  "mqtt_connect" : settings.MQTT_CONNECT,
                                                  "form": form})
    else:
        print("Connect Ok")
        print(settings.DSE_CONNECT, settings.DSE_KEYSPACE, settings.DSE_POPULATED)
        print(settings.MQTT_CONNECT)
        
        if not settings.DSE_KEYSPACE or not settings.DSE_POPULATED:
            return redirect("administration:home")
        
        
        if (
            not isinstance(request.user, AnonymousUser)
            and request.user
            and request.user.is_authenticated()
            ):
            return redirect("archive:home")
        else:
            return render(request, "index.html", {"dse_connect" : settings.DSE_CONNECT,
                                                  "mqtt_connect" : settings.MQTT_CONNECT,
                                                  "form": None})




