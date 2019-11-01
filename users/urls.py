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

from django.conf.urls import url

from . import views

app_name = "users"

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^login$', views.userlogin, name='auth_login'),
    url(r'^logout$', views.userlogout, name='auth_logout'),
    
    url(r'^new/user$', views.new_user, name='new_user'),
    url(r'^delete/user/(?P<name>.*)$', views.delete_user, name='delete_user'),
    url(r'^edit/user/(?P<name>.*)$', views.edit_user, name='edit_user'),
    
    url(r'^(?P<name>.*)$', views.user_view, name='view'),

]
