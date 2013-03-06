import sublime
import sublime_plugin
import urllib2
import re
import base64
import json


class ServiceNowBuildListener(sublime_plugin.EventListener):
    def on_pre_save(self, view):
        view.run_command('service_now_build')


class ServiceNowBuildCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.timeout = 5

        # Get the body of the file
        reg = sublime.Region(0, self.view.size())
        self.text = self.view.substr(reg)

        # Get the file URL from the comment in the file
        url_match = self.get_url(self.text)
        if url_match:
            url = url_match.groups()[0]
        else:
            print "Not a ServiceNow File"
            return

        # Get the instance name from the URL
        instance = self.get_instance(url)

        if not instance:
            print "No instance found"
            return

        # Get the field name from the comment in the file
        fieldname = self.get_fieldname(self.text)
        
        if not fieldname:
            fieldname = "script"
            print "No fieldname found, using default 'script'"
            
        # Get the Base64 encoded Auth String
        authentication = self.get_authentication(edit, instance)

        if authentication:
            authentication = "Basic " + authentication
        else:
            print "No authentication found"
            return

        try:
            data = json.dumps({fieldname: self.text})
            url = url + "&sysparm_action=update&JSON"
            url = url.replace("sys_id", "sysparm_query=sys_id")
            request = urllib2.Request(url, data)
            request.add_header("Authorization", authentication)
            request.add_header("Content-type", "application/json")
            http_file = urllib2.urlopen(request, timeout=self.timeout)
            self.result = http_file.read()
            print "File Successully Uploaded"
            return
        except (urllib2.HTTPError) as (e):
            err = 'Error %s' % (str(e.code))
        except (urllib2.URLError) as (e):
            err = 'Error %s' % (str(e.code))

        print err

    def get_authentication(self, edit, instance):
        settings = sublime.load_settings('SN.sublime-settings')
        reg = sublime.Region(0, self.view.size())
        text = self.view.substr(reg)

        authMatch = re.search(r"__authentication[\W=]*([a-zA-Z0-9:~`\!@#$%\^&*()_\-;,.]*)", text)

        if authMatch and authMatch.groups()[0] != "STORED":
            user_pass = authMatch.groups()[0]
            authentication = self.store_authentication(edit, user_pass, instance)
        else:
            authentication = settings.get(instance)

        if authentication:
            return authentication
        else:
            return False

    def store_authentication(self, edit, authentication, instance):
        base64string = base64.encodestring(authentication).replace('\n', '')
        reg = sublime.Region(0, self.view.size())
        text = self.view.substr(reg)
        self.text = text.replace(authentication, "STORED")
        self.view.replace(edit, reg, self.text)

        settings = sublime.load_settings('SN.sublime-settings')
        settings.set(instance, base64string)
        settings = sublime.save_settings('SN.sublime-settings')

        return base64string

    def get_fieldname(self, text):
        fieldname_match = re.search(r"__fieldName[\W=]*([a-zA-Z0-9_]*)", text)
        if fieldname_match:
            return fieldname_match.groups()[0]
        else:
            return False

    def get_url(self, text):
        return re.search(r"__fileURL[\W=]*([a-zA-Z0-9:/.\-_?&=]*)", text)

    def get_instance(self, url):
        instance_match = re.search(r"//([a-zA-Z0-9]*)\.", url)
        if instance_match:
            return instance_match.groups()[0]
        else:
            return False
