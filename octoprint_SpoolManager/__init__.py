# coding=utf-8
from __future__ import absolute_import

import math
from datetime import datetime
import flask
import octoprint.plugin
from flask import request
from octoprint.events import Events
from octoprint.util.comm import MachineCom

from octoprint_SpoolManager.DatabaseManager import DatabaseManager
from octoprint_SpoolManager.Odometer import FilamentOdometer
from octoprint_SpoolManager.api import Transformer
from octoprint_SpoolManager.api.SpoolManagerAPI import SpoolManagerAPI
from octoprint_SpoolManager.common import StringUtils
from octoprint_SpoolManager.common.SettingsKeys import SettingsKeys

class SpoolmanagerPlugin(
							SpoolManagerAPI,
							octoprint.plugin.SimpleApiPlugin,
							octoprint.plugin.SettingsPlugin,
                            octoprint.plugin.AssetPlugin,
                            octoprint.plugin.TemplatePlugin,
							octoprint.plugin.StartupPlugin,
							octoprint.plugin.EventHandlerPlugin,
):

	def initialize(self):
		self._logger.info("Start initializing")

		# DATABASE
		self.databaseConnectionProblemConfirmed = False
		sqlLoggingEnabled = self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_SQL_LOGGING_ENABLED])
		self._databaseManager = DatabaseManager(self._logger, sqlLoggingEnabled)

		databaseSettings = self._buildDatabaseSettingsFromPluginSettings()

		# init database
		self._databaseManager.initDatabase(databaseSettings, self._sendMessageToClient)


		# OTHER STUFF
		self._filamentOdometer = None
		self._filamentOdometer = FilamentOdometer()
		# TODO no idea what this thing is doing in detail self._filamentOdometer.set_g90_extruder(self._settings.getBoolean(["feature", "g90InfluencesExtruder"]))

		self._filamentManagerPluginImplementation = None
		self._filamentManagerPluginImplementationState = None

		self._lastPrintState = None

		self.metaDataFilamentLength = None

		self.alreadyCanceled = False

		self._logger.info("Done initializing")
		pass


	################################################################################################### public functions

	def checkRemainingFilament(self):

		shouldWarn = self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_WARN_IF_FILAMENT_NOT_ENOUGH])
		if (shouldWarn == False):
			return True

		# - check, if spool change in pause-mode

		# - check if new spool fits for current printjob
		selectedSpool = self.loadSelectedSpool()

		if (selectedSpool == None or self.metaDataFilamentLength == None):
			return False

		# need attributes present: diameter, density, totalWeight
		warningMessage = "Following fields not set in Spool '" + selectedSpool.displayName + "': "
		missing = False

		diameter = selectedSpool.diameter
		density = selectedSpool.density
		totalWeight = selectedSpool.totalWeight
		usedWeight = selectedSpool.usedWeight
		if (diameter == None):
			missing = True
			warningMessage += "diameter "
		if (density == None):
			missing = True
			warningMessage += "density "
		if (totalWeight == None):
			missing = True
			warningMessage += "total weight"
		if (usedWeight == None):
			usedWeight = 0.0

		if (missing == True):
			self._sendMessageToClient("warning", "Filament prediction not possible!", warningMessage)
			return False

		warningMessage = "One of the needed fields are not a number in Spool '" + selectedSpool.displayName + "': "
		notANumber = False
		try:
			diameter = float(diameter)
		except ValueError:
			notANumber = True
			warningMessage += "diameter "
		try:
			density = float(density)
		except ValueError:
			notANumber = True
			warningMessage += "density "
		try:
			totalWeight = float(totalWeight)
		except ValueError:
			notANumber = True
			warningMessage += "total weight "
		try:
			usedWeight = float(usedWeight)
		except ValueError:
			notANumber = True
			warningMessage += "used weight "

		if (notANumber == True):
			self._sendMessageToClient("warning", "Filament prediction not possible!", warningMessage)
			return False

		# Benötigtes Gewicht = gewicht(geplante länge, durchmesser, dichte)
		requiredWeight = int(self._calculateWeight(self.metaDataFilamentLength, diameter, density))

		# Vorhanden Gewicht = Gesamtgewicht - Verbrauchtes Gewicht
		remainingWeight = totalWeight - usedWeight

		if (remainingWeight < requiredWeight):
			self._sendMessageToClient("warning", "Filament not enough!",
									  "Required '" + str(requiredWeight) + "g' available from Spool '" + str(remainingWeight) + "g'!")
			return False
		return True


	################################################################################################## private functions

	def _sendDataToClient(self, payloadDict):
		self._plugin_manager.send_plugin_message(self._identifier,
												 payloadDict)



	def _sendMessageToClient(self, type, title, message):
		self._logger.warning("SendToClient: " + type + "#" + title + "#" + message)
		title = "SPM:" + title
		self._sendDataToClient(dict(action="showPopUp",
									type=type,
									title= title,
									message=message))


	def _checkForMissingPluginInfos(self, sendToClient=False):

		pluginInfo = self._getPluginInformation("filamentmanager")
		self._filamentManagerPluginImplementationState  = pluginInfo[0]
		self._filamentManagerPluginImplementation = pluginInfo[1]

		self._logger.info("Plugin-State: "
						  "filamentmanager=" + self._filamentManagerPluginImplementationState + " ")
		pass

	# get the plugin with status information
	# [0] == status-string
	# [1] == implementaiton of the plugin
	def _getPluginInformation(self, pluginKey):

		status = None
		implementation = None

		if pluginKey in self._plugin_manager.plugins:
			plugin = self._plugin_manager.plugins[pluginKey]
			if plugin != None:
				if (plugin.enabled == True):
					status = "enabled"
					# for OP 1.4.x we need to check agains "icompatible"-attribute
					if (hasattr(plugin, 'incompatible') ):
						if (plugin.incompatible == False):
							implementation = plugin.implementation
						else:
							status = "incompatible"
					else:
						# OP 1.3.x
						implementation = plugin.implementation
					pass
				else:
					status = "disabled"
		else:
			status = "missing"

		return [status, implementation]


	def _calculateWeight(self, length, diameter, density):
		radius = diameter / 2.0;
		volume = length * math.pi * (radius * radius) / 1000
		result = volume * density
		return result

	def _buildDatabaseSettingsFromPluginSettings(self):
		databaseSettings = DatabaseManager.DatabaseSettings()
		databaseSettings.useExternal = self._settings.get([SettingsKeys.SETTINGS_KEY_DATABASE_USE_EXTERNAL])
		databaseSettings.type = self._settings.get([SettingsKeys.SETTINGS_KEY_DATABASE_TYPE])
		databaseSettings.host = self._settings.get([SettingsKeys.SETTINGS_KEY_DATABASE_HOST])
		databaseSettings.port = self._settings.get_int([SettingsKeys.SETTINGS_KEY_DATABASE_PORT])
		databaseSettings.name = self._settings.get([SettingsKeys.SETTINGS_KEY_DATABASE_NAME])
		databaseSettings.user = self._settings.get([SettingsKeys.SETTINGS_KEY_DATABASE_USER])
		databaseSettings.password = self._settings.get([SettingsKeys.SETTINGS_KEY_DATABASE_PASSWORD])
		pluginDataBaseFolder = self.get_plugin_data_folder()
		databaseSettings.baseFolder = pluginDataBaseFolder
		databaseSettings.fileLocation = self._databaseManager.buildDefaultDatabaseFileLocation(databaseSettings.baseFolder)

		return databaseSettings



	# common states: STATE_CONNECTING("Connecting"), STATE_OPERATIONAL("Operational"),
	# STATE_STARTING("Startinf..."), STATE_PRINTING("Printing or Sendind"), STATE_CANCELLING("Cancelling"),
	# STATE_PAUSING("Pausing"), STATE_PAUSED("Paused"), STATE_RESUMING("Resuming"), STATE_FINISHING("Finishing"), STATE_CLOSED("Offline")
	# Normal flow:
	# - OPERATIONAL
	# - STARTING
	# - PRINTING
	# - FINISHING
	# - OPERATIONAL

	# Cancel
	# - ...
	# - PRINTING
	# -CANCELLING
	# - OPERATIONAL

	# Pause -> Resume
	# - STARTING
	# - PRINTING
	# - PAUSING
	# - PAUSED
	# - RESUMING
	# - PRINTING
	# - FINISHING
	# - OPERATIONAL


	# Pause -> Restart
	# - PRINTING
	# - PAUSING
	# - PAUSED
	# - STARTING
	# - PRINTING
	# def _on_printer_state_changed(self, payload):
	# 	printerState = payload['state_id']
	# 	print("######################  " +str(printerState))
	# 	if payload['state_id'] == "PRINTING":
	# 		if self._lastPrintState == "PAUSED":
	# 			# resuming print
	# 			self.filamentOdometer.reset_extruded_length()
	# 		else:
	# 			# starting new print
	# 			self.filamentOdometer.reset()
	# 		self.odometerEnabled = self._settings.getBoolean(["enableOdometer"])
	# 		self.pauseEnabled = self._settings.getBoolean(["autoPause"])
	# 		self._logger.debug("Printer State: %s" % payload["state_string"])
	# 		self._logger.debug("Odometer: %s" % ("On" if self.odometerEnabled else "Off"))
	# 		self._logger.debug("AutoPause: %s" % ("On" if self.pauseEnabled and self.odometerEnabled else "Off"))
	# 	elif self._lastPrintState == "PRINTING":
	# 		# print state changed from printing => update filament usage
	# 		self._logger.debug("Printer State: %s" % payload["state_string"])
	# 		if self.odometerEnabled:
	# 			self.odometerEnabled = False  # disabled because we don't want to track manual extrusion
	#
	# 			self.currentExtrusion = self.filamentOdometer.get_extrusion()
	#
	# 	# update last print state
	# 	self._lastPrintState = payload['state_id']

	def _on_printJobStarted(self):
		# starting new print
		self._filamentOdometer.reset()

		spoolModel = self.loadSelectedSpool()
		if (spoolModel != None):
			if (StringUtils.isEmpty(spoolModel.firstUse) == True):
				firstUse = datetime.now()
				spoolModel.firstUse = firstUse
				self._databaseManager.saveSpool(spoolModel)
				self._sendDataToClient(dict(
											action="reloadTable"
											))
		pass

	#### print job finished
	def _on_printJobFinished(self, printStatus, payload):

		spoolModel = self.loadSelectedSpool()
		if (spoolModel == None):
			self._logger.warning("No spool selected, could not update values after print")
			return

		# - Last usage datetime
		lastUsage = datetime.now()
		spoolModel.lastUse = lastUsage
		# - Used length
		currentExtrusionForAllTools = self._filamentOdometer.getExtrusionForAllTools()
		# if (len(currentExtrusionForAllTools) == 0):
		# 	self._logger.warning("Odomenter could not detect any extrusion")
		# 	return
		currentExtrusionLenght = currentExtrusionForAllTools # TODO Support of multi-tool
		self._logger.info("Extruded filament length: " + str(currentExtrusionLenght))
		spoolUsedLength = 0.0 if StringUtils.isEmpty(spoolModel.usedLength) == True else spoolModel.usedLength
		self._logger.info("Current Spool filament length: " + str(spoolUsedLength))
		newUsedLength = spoolUsedLength + currentExtrusionLenght
		self._logger.info("New Spool filament length: " + str(newUsedLength))
		spoolModel.usedLength = newUsedLength
		# - Used weight
		diameter = spoolModel.diameter
		density = spoolModel.density
		if (diameter == None or  density == None):
			self._logger.warning("Could not update spool weight, because diameter or density not set in spool '"+spoolModel.displayName+"'")
		else:
			usedWeight = self._calculateWeight(currentExtrusionLenght, diameter, density)
			spoolUsedWeight = 0.0 if spoolModel.usedWeight == None else spoolModel.usedWeight
			newUsedWeight = spoolUsedWeight + usedWeight
			spoolModel.usedWeight = newUsedWeight

		self._databaseManager.saveSpool(spoolModel)
		self._sendDataToClient(dict(
									action = "reloadTable and sidebarSpools"
									))
		pass

	def _on_clientOpened(self, payload):
		# start-workaround https://github.com/foosel/OctoPrint/issues/3400
		import time
		time.sleep(3)
		selectedSpoolsAsDicts = []

		# Check if database is available
		# connected = self._databaseManager.reConnectToDatabase()
		# self._logger.info("ClientOpened. Database connected:"+str(connected))

		connectionErrorResult = self._databaseManager.testDatabaseConnection()

		# Don't show already shown message
		if (self.databaseConnectionProblemConfirmed == False and
			connectionErrorResult != None):
			databaseErrorMessageDict = self._databaseManager.getCurrentErrorMessageDict();
			# The databaseErrorMessages should always be present in that case.
			if (databaseErrorMessageDict != None):
				self._logger.error(databaseErrorMessageDict)
				self._sendDataToClient(dict(action = "showConnectionProblem",
											type = databaseErrorMessageDict["type"],
											title = databaseErrorMessageDict["title"],
											message = databaseErrorMessageDict["message"]))

		# Send plugin storage information
		## Storage
		if (connectionErrorResult == None):
			selectedSpoolsAsDicts = [
				(None if selectedSpool is None else Transformer.transformSpoolModelToDict(selectedSpool))
				for selectedSpool in self.loadSelectedSpools()
			]

		pluginNotWorking = connectionErrorResult != None
		self._sendDataToClient(dict(action = "initalData",
									selectedSpools = selectedSpoolsAsDicts,
									isFilamentManagerPluginAvailable = self._filamentManagerPluginImplementation != None,
									pluginNotWorking = pluginNotWorking
									))

		pass

	def _on_clientClosed(self, payload):
		self.databaseConnectionProblemConfirmed = False

	def _on_file_selectionChanged(self, payload):
		if ("origin" in payload and "path" in payload):
			metadata = self._file_manager.get_metadata(payload["origin"], payload["path"])
			if ("analysis" in metadata):
				if ("filament" in metadata["analysis"]):
					allFilemants = metadata["analysis"]["filament"]
					# TODO support multiple tools and not only tool0 (or first you got)
					if (allFilemants):
						for toolIndex in range(5):
							toolName = "tool" + str(toolIndex)
							if (toolName in allFilemants):
								self.metaDataFilamentLength = allFilemants[toolName]["length"]
								self.checkRemainingFilament()
						return

		self.metaDataFilamentLength = 0.0

	pass
	######################################################################################### Hooks and public functions

	def on_after_startup(self):
		# check if needed plugins were available
		self._checkForMissingPluginInfos()
		pass

	# Listen to all  g-code which where already sent to the printer (thread: comm.sending_thread)
	def on_sentGCodeHook(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):

		# TODO maybe later via a queue
		self._filamentOdometer.parse(gcode, cmd)
		# if self.pauseEnabled and self.check_threshold():
		# 	self._logger.info("Filament is running out, pausing print")
		# 	self._printer.pause_print()
		pass

	def on_event(self, event, payload):

		# if event == Events.PRINTER_STATE_CHANGED:
		if (Events.CLIENT_OPENED == event):
			self._on_clientOpened(payload)
			return
		if (Events.CLIENT_CLOSED == event):
			self._on_clientClosed(payload)
			return

		elif (Events.PRINT_STARTED == event):
			self.alreadyCanceled = False
			self._on_printJobStarted()

		elif (Events.PRINT_DONE == event):
			self._on_printJobFinished("success", payload)

		elif (Events.PRINT_FAILED == event):
			if self.alreadyCanceled == False:
				self._on_printJobFinished("failed", payload)

		elif (Events.PRINT_CANCELLED == event):
			self.alreadyCanceled = True
			self._on_printJobFinished("canceled", payload)

		if (Events.FILE_SELECTED == event or
			Events.FILE_DESELECTED == event or
			Events.UPDATED_FILES == event):
			self._on_file_selectionChanged(payload)
			return

		pass


	def on_settings_save(self, data):
		# # default save function
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
		#
		# databaseSettings = self._buildDatabaseSettingsFromPluginSettings()
		#
		# self._databaseManager.assignNewDatabaseSettings(databaseSettings)
		# testResult = self._databaseManager.testDatabaseConnection(databaseSettings)
		# if (testResult != None):
		# 	# TODO Send to client
		# 	pass



	# to allow the frontend to trigger an update
	def on_api_get(self, request):
		if len(request.values) != 0:
			action = request.values["action"]

			# deceide if you want the reset function in you settings dialog
			if "isResetSettingsEnabled" == action:
				return flask.jsonify(enabled="true")

			if "resetSettings" == action:
				self._settings.set([], self.get_settings_defaults())
				self._settings.save()
				return flask.jsonify(self.get_settings_defaults())

			# because of some race conditions, we can't push the initalDate during client-open event. So we provide the settings on request
			if "additionalSettingsValues" == action:
				return flask.jsonify({
					"isFilamentManagerPluginAvailable":self._filamentManagerPluginImplementation != None
				})

	##~~ SettingsPlugin mixin
	def get_settings_defaults(self):

		settings = dict()

		# Not visible
		settings[SettingsKeys.SETTINGS_KEY_SELECTED_SPOOL_DATABASE_ID] = None
		settings[SettingsKeys.SETTINGS_KEY_SELECTED_SPOOLS_DATABASE_IDS] = []
		settings[SettingsKeys.SETTINGS_KEY_HIDE_EMPTY_SPOOL_IN_SIDEBAR] = False
		settings[SettingsKeys.SETTINGS_KEY_HIDE_INACTIVE_SPOOL_IN_SIDEBAR] = True
		## Genral
		settings[SettingsKeys.SETTINGS_KEY_REMINDER_SELECTING_SPOOL] = True
		settings[SettingsKeys.SETTINGS_KEY_WARN_IF_SPOOL_NOT_SELECTED] = True
		settings[SettingsKeys.SETTINGS_KEY_WARN_IF_FILAMENT_NOT_ENOUGH] = True
		settings[SettingsKeys.SETTINGS_KEY_CURRENCY_SYMBOL] = "€"

		## QR-Code
		settings[SettingsKeys.SETTINGS_KEY_QR_CODE_ENABLED] = True
		settings[SettingsKeys.SETTINGS_KEY_QR_CODE_FILL_COLOR] = "darkgreen"
		settings[SettingsKeys.SETTINGS_KEY_QR_CODE_BACKGROUND_COLOR] = "white"
		settings[SettingsKeys.SETTINGS_KEY_QR_CODE_WIDTH] = "100"
		settings[SettingsKeys.SETTINGS_KEY_QR_CODE_HEIGHT] = "100"

		## Export / Import
		settings[SettingsKeys.SETTINGS_KEY_IMPORT_CSV_MODE] = SettingsKeys.KEY_IMPORTCSV_MODE_APPEND

		## Debugging
		settings[SettingsKeys.SETTINGS_KEY_SQL_LOGGING_ENABLED] = False

		## Database
		## nested settings are not working, because if only a few attributes are changed it only returns these few attribuets, instead the default values + adjusted values
		settings[SettingsKeys.SETTINGS_KEY_DATABASE_USE_EXTERNAL] = False
		datbaseLocation = DatabaseManager.buildDefaultDatabaseFileLocation(self.get_plugin_data_folder())
		settings[SettingsKeys.SETTINGS_KEY_DATABASE_LOCAL_FILELOCATION] = datbaseLocation
		settings[SettingsKeys.SETTINGS_KEY_DATABASE_TYPE] = "sqlite"
		# settings[SettingsKeys.SETTINGS_KEY_DATABASE_TYPE] = "postgres"
		settings[SettingsKeys.SETTINGS_KEY_DATABASE_HOST] = "localhost"
		settings[SettingsKeys.SETTINGS_KEY_DATABASE_PORT] = 5432
		settings[SettingsKeys.SETTINGS_KEY_DATABASE_NAME] = "SpoolDatabase"
		settings[SettingsKeys.SETTINGS_KEY_DATABASE_USER] = "Olli"
		settings[SettingsKeys.SETTINGS_KEY_DATABASE_PASSWORD] = "illO"
		# {
		# 	"localDatabaseFileLocation": "",
		# 	"type": "postgres",
		# 	"host": "localhost",
		# 	"port": 5432,
		# 	"databaseName": "SpoolDatabase",
		# 	"user": "Olli",
		# 	"password": "illO"
		# }

		return settings

	##~~ TemplatePlugin mixin
	def get_template_configs(self):
		return [
			dict(type="tab", name="Spools"),
			dict(type="settings", custom_bindings=True, name="Spool Manager")
		]

	##~~ AssetPlugin mixin
	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=[
				"js/quill.min.js",
				"js/select2.min.js",
				"js/jquery.datetimepicker.full.min.js",
				"js/tinycolor.js",
				"js/pick-a-color.js",
				"js/ResetSettingsUtilV3.js",
				"js/ComponentFactory.js",
				"js/TableItemHelper.js",
				"js/SpoolManager.js",
				"js/SpoolManager-APIClient.js",
				"js/SpoolManager-EditSpoolDialog.js",
				"js/SpoolManager-ImportDialog.js",
				"js/SpoolManager-DatabaseConnectionProblemDialog.js"
			],
			css=[
				"css/quill.snow.css",
				"css/select2.min.css",
				"css/jquery.datetimepicker.min.css",
				"css/pick-a-color-1.1.8.min.css",
				"css/SpoolManager.css"
			],
			less=["less/SpoolManager.less"]
		)

	##~~ Softwareupdate hook
	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
		# for details.
		return dict(
			SpoolManager=dict(
				displayName="SpoolManager Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="OllisGit",
				repo="OctoPrint-SpoolManager",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/OllisGit/OctoPrint-SpoolManager/releases/latest/download/master.zip"
			)
		)


	def message_on_connect(self, comm, script_type, script_name, *args, **kwargs):
		print(script_name)
		if not script_type == "gcode" or not script_name == "afterPrinterConnected":
			return None

		prefix = None
		postfix = "M117 OctoPrint connected"
		variables = dict(myvariable="Hi! I'm a variable!")
		return prefix, postfix, variables

# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "SpoolManager Plugin"
__plugin_pythoncompat__ = ">=2.7,<4"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = SpoolmanagerPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.comm.protocol.gcode.sent": __plugin_implementation__.on_sentGCodeHook,
		"octoprint.comm.protocol.scripts": __plugin_implementation__.message_on_connect
	}

