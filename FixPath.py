from __future__ import division, absolute_import, print_function, unicode_literals
import sublime, sublime_plugin
import re, platform
from os import environ
from subprocess import Popen, PIPE


def isMac():
	if platform.system() == "Darwin":
		return True
	else:
		return False


if isMac():
	fixPathSettings = None
	originalEnv = {}


	def getEnvVar(name):
		global config

		command = "TERM=ansi CLICOLOR=\"\" SUBLIME=1 /usr/bin/login -fqpl $USER $SHELL "

		# If interactive shell
		if ('interactive' not in config) or (config['interactive'] == True):
			command += "-i "

		command += "-l -c 'TERM=ansi CLICOLOR=\"\" SUBLIME=1 printf \"%s\" \"$" + name + "\"'"

		# Execute command with original environ. Otherwise, our changes to the PATH propogate down to
		# the shell we spawn, which re-adds the system path & returns it, leading to duplicate values.
		var = Popen(command, stdout=PIPE, shell=True, env=originalEnv).stdout.read()

		varString = var.decode("utf-8")
		# Remove ANSI control characters (see: http://www.commandlinefu.com/commands/view/3584/remove-color-codes-special-characters-with-sed )
		varString = re.sub(r'\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]', '', varString)
		varString = varString.strip().rstrip(':')

		# Decode the byte array into a string, remove trailing whitespace, remove trailing ':'
		return varString


	def fixEnvVar(name):
		currVar = getEnvVar(name)

		# Basic sanity check to make sure our new var is not empty
		if len(currVar) > 0:
			environ[name] = currVar


	def fixPath():
		global userPreferences
		global config

		# Load config from User Preferences
		config = userPreferences.get("fix_mac_path", {})

		# Fix PATH by default
		fixEnvVar("PATH")

		# Fix other env vars provided in config
		if 'env_vars' in config:
			for envVar in config['env_vars']:
				fixEnvVar(envVar)

		# Append additional path items provided by user preferences
		if 'additional_path_item' in config:
			for pathItem in config['additional_path_item']:
				environ['PATH'] = pathItem + ':' + environ['PATH']

		return True


	def plugin_loaded():
		global userPreferences

		userPreferences = sublime.load_settings("Preferences.sublime-settings")
		userPreferences.clear_on_change('fixpath-reload')
		userPreferences.add_on_change('fixpath-reload', fixPath)

		# Save the original environ (particularly the original PATH) to restore later
		global originalEnv

		for key in environ:
			originalEnv[key] = environ[key]

		fixPath()


	def plugin_unloaded():
		# When we unload, reset PATH to original value. Otherwise, reloads of this plugin will cause
		# the PATH to be duplicated.
		environ['PATH'] = originalEnv['PATH']

		# Reset other env vars
		global config
		if 'env_vars' in config:
			for envVar in config['env_vars']:
				if envVar in environ:
					del environ[envVar]

		global userPreferences
		userPreferences.clear_on_change('fixpath-reload')


	# Sublime Text 2 doesn't have loaded/unloaded handlers, so trigger startup code manually, first
	# taking care to clean up any messes from last time.
	if int(sublime.version()) < 3000:
		# Stash the original PATH in the env variable _ST_ORIG_PATH.
		if environ.has_key('_ST_ORIG_PATH'):
			# If _ST_ORIG_PATH exists, restore it as the true path.
			environ['PATH'] = environ['_ST_ORIG_PATH']
		else:
			# If it doesn't exist, create it
			environ['_ST_ORIG_PATH'] = environ['PATH']

		plugin_loaded()



else:	# not isMac()
	print("FixMacPath will not be loaded because current OS is not Mac OS X ('Darwin'). Found '" + platform.system() + "'")
