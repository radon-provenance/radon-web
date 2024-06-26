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

import json
from django.forms import Widget
from django.utils.safestring import mark_safe
from django.forms.utils import flatatt


class JsonPairInputs(Widget):
    """A widget that displays JSON Key Value Pairs
    as a list of text input box pairs
 
    Usage (in forms.py) :
    examplejsonfield = forms.CharField(label  = "Example JSON Key Value Field", required = False,
                                       widget = JsonPairInputs(val_attrs={'size':35},
                                                               key_attrs={'class':'large'}))

    """

    def __init__(self, *args, **kwargs):
        """A widget that displays JSON Key Value Pairs
        as a list of text input box pairs

        kwargs:
        key_attrs -- html attributes applied to the 1st input box pairs
        val_attrs -- html attributes applied to the 2nd input box pairs

        """
        self.key_attrs = {}
        self.val_attrs = {}
        if "key_attrs" in kwargs:
            self.key_attrs = kwargs.pop("key_attrs")
        if "val_attrs" in kwargs:
            self.val_attrs = kwargs.pop("val_attrs")
        Widget.__init__(self, *args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        """Renders this widget into an html string
 
        args:
        name  (str)  -- name of the field
        value (str)  -- a json string of a two-tuple list automatically passed in by django
        attrs (dict) -- automatically passed in by django (unused in this function)
        """

        if (not value) or value.strip() == "":
            value = '{"":""}'
        twotuple = json.loads(value)

        if isinstance(twotuple, dict):
            twotuple = [(k, v,) for k, v in twotuple.items()]
        if not twotuple:
            twotuple = [("", "")]

        ret = ""
        if value and len(value) > 0:
            for k, v in twotuple:
                ctx = {
                    "key": k,
                    "value": v,
                    "fieldname": name,
                    "key_attrs": flatatt(self.key_attrs),
                    "val_attrs": flatatt(self.val_attrs),
                }
                ret += (
                    """
                    <div class="form-group row my-2" id="">
                      
                        <div class="col-md-4">
                            <input placeholder="Key" 
                                   class="form-control" 
                                   type="text" 
                                   name="json_key[%(fieldname)s]" 
                                   value="%(key)s" %(key_attrs)s>
                        </div>
                        <div class="col-md-1 text-center">
                          <span class="align-middle fs-4">=</span>
                        </div>
                        <div class="col-md-5">
                            <input placeholder="Value" 
                                   class="form-control" 
                                   type="text" 
                                   name="json_value[%(fieldname)s]" 
                                   value="%(value)s" %(val_attrs)s>
                        </div>
                        <div class="col-md-2 btn-group" role="group">
                            <a class="btn btn-success btn-sm mx-1 my-1">+</a>
                            <a class="btn btn-danger btn-sm mx-1 my-1">-</a>
                        </div>
                        <div class="clearfix"></div>
                        
                    </div>
                    """
                    % ctx
                )
        ret = '<span id="metadata_fields">' + ret + "</span>"
        return mark_safe(ret)


    def value_from_datadict(self, data, files, name):
        """
        Returns the json representation of the key-value pairs
        sent in the POST parameters

        args:
        data  (dict)  -- request.POST or request.GET parameters
        files (list)  -- request.FILES
        name  (str)   -- the name of the field associated with this widget

        """
        jsontext = ""
        if "json_key[%s]" % name in data and "json_value[%s]" % name in data:
            keys = data.getlist("json_key[%s]" % name)
            values = data.getlist("json_value[%s]" % name)
            twotuple = []
            for key, value in zip(keys, values):
                if len(key) > 0:
                    twotuple += [(key, value)]
            jsontext = json.dumps(twotuple)
        return jsontext
