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

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import AnonymousUser


def home(request):
    if (
        not isinstance(request.user, AnonymousUser)
        and request.user
        and request.user.is_authenticated()
    ):
        return redirect("archive:home")
    return render(request, "index.html", {})


def index(request):
    return HttpResponse("Hello, world!")
