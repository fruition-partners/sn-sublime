sn-sublime
==========

Sublime Integration with ServiceNow


Setting an instance
==========

All files that will be set to an instance must have a comment in the top with the URL for the file

Example

  // __fileURL = https://fruition18.service-now.com/sys_ui_script.do?sys_id=db89dc86456b70c884e9262b8aecf165

Storing Credentials
==========

Credentials are stored as a Base64 encoded string within the settings for the plugin.
To add credentials create a comment to the top of the file with the user name and password separated by a :

   // __authentication = user:pass

The user name and password will be replaced with the word "STORED" if the command completed
  
Credentials only need to be set once on any file that is set to an instance
