import sublime
import sublime_plugin
import urllib
import urllib2
import threading
import re
import base64
import json

class serviceNowBuildCommand(sublime_plugin.TextCommand):  
	def run(self, edit):  
		self.timeout = 5
		settings = sublime.load_settings('SN.sublime-settings')

		# Get the body of the file
		reg = sublime.Region(0, self.view.size())
		self.text = self.view.substr(reg)

		# Get the file URL from the comment in the file
		urlMatch = re.search(r"__fileURL[\W=]*([a-zA-Z0-9:/.\-_?&=]*)", self.text)
		if urlMatch:
			url = urlMatch.groups()[0]
		else:
			sublime.message_dialog("No Instance Comment Found.")
			return

		# Get the instance name from the URL
		instanceMatch = re.search(r"//([a-zA-Z0-9]*)\.", url)
		instance = instanceMatch.groups()[0]

		authentication = settings.get( instance )

		if authentication:
			authentication = "Basic " + authentication
		else:
			sublime.message_dialog("No authentication found")
			return

		try:  
			data = json.dumps({"script" : self.text })
			request = urllib2.Request(url, data)
			request.add_header("Authorization", authentication)
			request.add_header("Content-type", "application/json")  			
			http_file = urllib2.urlopen(request, timeout=self.timeout)  
			self.result = http_file.read()  
			return  
		except (urllib2.HTTPError) as (e):  
			err = '%s: HTTP error %s contacting API' % (__name__, str(e.code))  
		except (urllib2.URLError) as (e):  
			err = '%s: URL error %s contacting API' % (__name__, str(e.reason))  
		sublime.error_message(err)  
		self.result = False

class serviceNowStoreAuthCommand(sublime_plugin.TextCommand):
	def getAuthentication(self, edit):
		reg = sublime.Region(0, self.view.size())
		text = self.view.substr(reg)

		urlMatch = re.search(r"__fileURL[\W=]*([a-zA-Z0-9:/.\-_?&=]*)", text)
		if urlMatch:
			url = urlMatch.groups()[0]
		else:
			sublime.message_dialog("No Instance Comment Found.")
			return

		# Get the instance name from the URL
		instanceMatch = re.search(r"//([a-zA-Z0-9]*)\.", url)
		instance = instanceMatch.groups()[0]

		authMatch = re.search(r"__authentication[\W=]*([a-zA-Z0-9:]*)", text)
		if authMatch:
			authentication = authMatch.groups()[0]
		else:
			sublime.message_dialog("No authentication information found.")
			return		

		base64string = base64.encodestring(authentication).replace('\n', '')
		text = text.replace(authentication, "STORED");
		self.view.replace(edit,reg,text)

		settings = sublime.load_settings('SN.sublime-settings')
		settings.set( instance, base64string )
		settings = sublime.save_settings('SN.sublime-settings')