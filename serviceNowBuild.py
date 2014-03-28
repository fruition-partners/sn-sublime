'''
Copyright (c) 2013 Fruition Partners, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

import sublime
import sublime_plugin
import urllib2
import re
import base64
import json


class ServiceNowBuildListener(sublime_plugin.EventListener):
    def on_pre_save(self, view):
        view.run_command('service_now_build')

    def on_load(self,view):
        sublime.set_timeout(syncFileCallback,10)
        

class ServiceNowBuildCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # Get the body of the file
        reg = sublime.Region(0, self.view.size())
        self.text = self.view.substr(reg)

        # Get the Base64 encoded Auth String
        authentication = get_authentication(self, edit)
        if not authentication:
            return

        # Get the field name from the comment in the file
        fieldname = get_fieldname(self.text)           

        try:
            data = json.dumps({fieldname: self.text})            
            url = self.url + "&sysparm_action=update&JSON"
            url = url.replace("sys_id", "sysparm_query=sys_id")
            result = http_call(authentication, url, data)
            print "SN-Sublime - File Successully Uploaded"
            return
        except (urllib2.HTTPError) as (e):
            err = 'SN-Sublime - HTTP Error: %s' % (str(e.code))
        except (urllib2.URLError) as (e):
            #Try again in case instance is using Dublin or later with JSONv2. Url is different
            try:
                url = self.url + "&sysparm_action=update&JSONv2"
                url = url.replace("sys_id", "sysparm_query=sys_id")
                result = http_call(authentication, url, data)
                print "File Successully Uploaded to SN"
                return
            except (urllib2.URLError) as (e):
                err = 'SN-Sublime - URL Error: %s' % (str(e))
        print err

        return
        

class ServiceNowSync(sublime_plugin.TextCommand):
    def run(self, edit):
        # Get the body of the file
        reg = sublime.Region(0, self.view.size())
        self.text = self.view.substr(reg)

        # Get the Base64 encoded Auth String
        authentication = get_authentication(self, edit)
        if not authentication:
           return

        try:
            url = self.url + "&sysparm_action=get&JSON"
            url = url.replace("sys_id", "sysparm_sys_id")
            response_data = json.loads(http_call(authentication,url,{}))
            serverText = response_data['records'][0]['script']

            if self.text != serverText and sublime.ok_cancel_dialog("File has been updated on server. \nPress OK to Reload."):
                self.view.erase(edit, reg)
                self.view.begin_edit()
                self.view.insert(edit,0,serverText)
                self.view.end_edit(edit)
            return
        except (urllib2.HTTPError) as (e):
            err = 'SN-Sublime - HTTP Error %s' % (str(e.code))
        except (urllib2.URLError) as (e):
            err = 'SN-Sublime - URL Error %s' % (str(e.code))
        print err
        

def http_call(authentication, url, data):
    timeout = 5
    request = urllib2.Request(url, data)
    request.add_header("Authorization", authentication)
    request.add_header("Content-type", "application/json")
    http_file = urllib2.urlopen(request, timeout=timeout)
    result = http_file.read()

    return result


def get_authentication(sublimeClass, edit):
    # Get the file URL from the comment in the file
    sublimeClass.url = get_url(sublimeClass.text)
    if not sublimeClass.url:
        return False

    # Get the instance name from the URL
    instance = get_instance(sublimeClass.url)
    if not instance:
        return False

    settings = sublime.load_settings('SN.sublime-settings')
    reg = sublime.Region(0, sublimeClass.view.size())
    text = sublimeClass.view.substr(reg)

    authMatch = re.search(r"__authentication[\W=]*([a-zA-Z0-9:~`\!@#$%\^&*()_\-;,.]*)", text)

    if authMatch and authMatch.groups()[0] != "STORED":
        user_pass = authMatch.groups()[0]
        authentication = store_authentication(sublimeClass, edit, user_pass, instance)
    else:
        authentication = settings.get(instance)

    if authentication:
        return "Basic " + authentication
    else:
        print "SN-Sublime - Auth Error. No authentication header tag found"        
        return False


def store_authentication(sublimeClass, edit, authentication, instance):
    base64string = base64.encodestring(authentication).replace('\n', '')
    reg = sublime.Region(0, sublimeClass.view.size())
    text = sublimeClass.view.substr(reg)
    sublimeClass.text = text.replace(authentication, "STORED")
    sublimeClass.view.replace(edit, reg, sublimeClass.text)

    settings = sublime.load_settings('SN.sublime-settings')
    settings.set(instance, base64string)
    settings = sublime.save_settings('SN.sublime-settings')

    return base64string

def get_fieldname(text):
    fieldname_match = re.search(r"__fieldName[\W=]*([a-zA-Z0-9_]*)", text)
    if fieldname_match:
        return fieldname_match.groups()[0]
    else:
        return 'script'

def get_url(text):
    url_match = re.search(r"__fileURL[\W=]*([a-zA-Z0-9:/.\-_?&=]*)", text)

    if url_match:
        return url_match.groups()[0]
    else:
        print "SN-Sublime - Error. Not a ServiceNow File"
        return False


def get_instance(url):
    instance_match = re.search(r"//([a-zA-Z0-9]*)\.", url)
    if instance_match:
        return instance_match.groups()[0]
    else:
        print "SN-Sublime - Error. No instance info found"        
        return False


def syncFileCallback():
    sublime.active_window().active_view().run_command('service_now_sync')
