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
# from octoprint_SpoolManager.Odometer import FilamentOdometer

from octoprint_SpoolManager.newodometer import NewFilamentOdometer

from octoprint_SpoolManager.api import Transformer
from octoprint_SpoolManager.api.SpoolManagerAPI import SpoolManagerAPI
from octoprint_SpoolManager.common import StringUtils
from octoprint_SpoolManager.common.SettingsKeys import SettingsKeys
from octoprint_SpoolManager.common.EventBusKeys import EventBusKeys

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
		# self._filamentOdometer = None
		# self._filamentOdometer = FilamentOdometer()
		# TODO no idea what this thing is doing in detail self._filamentOdometer.set_g90_extruder(self._settings.getBoolean(["feature", "g90InfluencesExtruder"]))

		self.myFilamentOdometer = NewFilamentOdometer(self._extrusionValuesChanged)
		self.myFilamentOdometer.set_g90_extruder(self._settings.get_boolean(["feature", "g90InfluencesExtruder"]))

		self._filamentManagerPluginImplementation = None
		self._filamentManagerPluginImplementationState = None

		self._lastPrintState = None

		self.metaDataFilamentLengths = []

		self.alreadyCanceled = False

		self._logger.info("Done initializing")
		pass

	################################################################################################### public functions

	def checkRemainingFilament(self, forToolIndex=None):
		"""
		Checks if all spools or single spool includes enough filament

		:param forToolIndex check only for the provided toolIndex
		:return: see
		"""
		shouldWarn = self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_WARN_IF_FILAMENT_NOT_ENOUGH])

		# - check, if spool change in pause-mode

		# - check if new spool fits for current printjob
		selectedSpools = self.loadSelectedSpools()

		requiredWeightResult = self._evaluateRequiredWeight(selectedSpools, forToolIndex, shouldWarn)
		# "metaDataMissing": metaDataMissing,
		# "warnUser": fromPluginSettings,
		# "attributesMissing": someAttributesMissing,
		# "notEnough": notEnough,
		# "detailedSpoolResult": [
		# 				"toolIndex": toolIndex,
		# 				"requiredWeight": requiredWeight,
		# 				"requiredLength": filamentLength,
		# 				"remainingWeight": remainingWeight,
		# 				"diameter": diameter,
		# 				"density": density,
		# 				"notEnough": notEnough,
		# 				"spoolSelected": True
		# ]

		# for a single check, don't send the info to the browser
		if (forToolIndex == None):
			requiredWeightResult["action"] = "requiredFilamentChanged"
			self._sendDataToClient(requiredWeightResult)

		return requiredWeightResult

	def set_temp_offsets(self, toolIndex, spoolModel):
		toolOffsetEnabled = self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_TOOL_OFFSET_ENABLED])
		bedOffsetEnabled = self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_BED_OFFSET_ENABLED])
		enclosureOffsetEnabled = self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_ENCLOSURE_OFFSET_ENABLED])

		offset_dict = dict()
		if (toolOffsetEnabled == True and spoolModel != None):
			# toolIndex should be tool0
			offset_dict["tool"+str(toolIndex)] = spoolModel.offsetTemperature if spoolModel.offsetTemperature is not None else 0

		if (bedOffsetEnabled == True and spoolModel != None):
			if (spoolModel.offsetBedTemperature != None):
				if (self._isNewOffsetTemperatureGreater("bed", spoolModel.offsetBedTemperature) == True):
					offset_dict["bed"] = spoolModel.offsetBedTemperature

		if (enclosureOffsetEnabled == True and spoolModel != None):
			if (spoolModel.offsetEnclosureTemperature != None):
				if (self._isNewOffsetTemperatureGreater("chamber", spoolModel.offsetEnclosureTemperature) == True):
					offset_dict["chamber"] = spoolModel.offsetEnclosureTemperature

		if (len(offset_dict) != 0):
			self._printer.set_temperature_offset(offset_dict)


	def _isNewOffsetTemperatureGreater(self, selectedOffset, newOffset):

		allTemperatures = self._printer.get_current_temperatures()
		selectedTemperature =  allTemperatures[selectedOffset] if selectedOffset in allTemperatures else None
		if (selectedTemperature != None):
			currentOffset = selectedTemperature["offset"]
			if (currentOffset != None and newOffset > currentOffset):
				return True
		return False


	def clear_temp_offsets(self):
		toolOffsetEnabled = self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_TOOL_OFFSET_ENABLED])
		bedOffsetEnabled = self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_BED_OFFSET_ENABLED])
		enclosureOffsetEnabled = self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_ENCLOSURE_OFFSET_ENABLED])

		offset_dict = dict()
		if (toolOffsetEnabled == True):
			printer_profile = self._printer_profile_manager.get_current_or_default()
			printerProfileToolCount = printer_profile['extruder']['count']
			# for toolIndex, filamentLength in enumerate(self.metaDataFilamentLengths):
			for toolIndex in range(printerProfileToolCount):
				# toolIndex should be tool0
				offset_dict["tool"+str(toolIndex)] = 0

		if (bedOffsetEnabled == True):
			offset_dict["bed"] = 0

		if (enclosureOffsetEnabled == True):
			offset_dict["chamber"] = 0

		if (len(offset_dict) != 0):
			self._printer.set_temperature_offset(offset_dict)

	################################################################################################## private functions

	def _sendDataToClient(self, payloadDict):
		self._plugin_manager.send_plugin_message(self._identifier,
												 payloadDict)

	def _sendMessageToClient(self, type, title, message, autoclose=False):
		self._logger.warning("SendToClient: " + type + "#" + title + "#" + message)
		self._sendDataToClient(dict(action="showPopUp",
									type=type,
									title= title,
									message=message,
									autoclose=autoclose))

	def _sendPayload2EventBus(self, eventKey, eventPayload):

		eventName = "plugin_spoolmanager_" + eventKey
		self._logger.debug("Send Event '"+eventName+"' with payload '"+str(eventPayload)+"' to event-bus")
		self._event_bus.fire(eventName, payload=eventPayload)

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

	def _extrusionValuesChanged(self, newExtrusionValues):
		if (self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_EXTRUSION_DEBUGGING_ENABLED])):
			self._sendDataToClient(dict(action="extrusionValuesChanged",
										extrusionValues=newExtrusionValues))

		pass

	def _readingFilamentMetaData(self):
		filamentLengthPresentInMeta = False
		self.metaDataFilamentLengths = []
		if ("job" in self._printer.get_current_data()):
			jobData = self._printer.get_current_data()["job"]
			if ("file" in jobData):
				fileData = jobData["file"]
				origin = fileData["origin"]
				path = fileData["path"]
				if (origin !=  None and path != None):
					metadata = self._file_manager.get_metadata(origin, path)
					if ("analysis" in metadata):
						if ("filament" in metadata["analysis"]):
							for toolName, toolData in metadata["analysis"]["filament"].items():
								toolIndex = int(toolName[4:])
								self.metaDataFilamentLengths += [0.0] * (toolIndex + 1 - len(self.metaDataFilamentLengths))
								self.metaDataFilamentLengths[toolIndex] = toolData["length"]
								filamentLengthPresentInMeta = True
		return filamentLengthPresentInMeta

	def _evaluateRequiredWeight(self, selectedSpools, forToolIndex=None, warnUser=False):

		self._readingFilamentMetaData()
		metaDataMissing = len(self.metaDataFilamentLengths) <= 0
		someAttributesMissing = False
		overallNotEnough = False
		requiredWeightResultDict = {
			"metaDataMissing": metaDataMissing,
			"warnUser": warnUser,
			"attributesMissing": someAttributesMissing,
			"notEnough": overallNotEnough,
			"detailedSpoolResult": []
		}
		if (metaDataMissing == True):
			return requiredWeightResultDict

		# loop over all tools
		for toolIndex, filamentLength in enumerate(self.metaDataFilamentLengths):
			if forToolIndex is not None and forToolIndex != toolIndex:
				continue
			selectedSpool = selectedSpools[toolIndex] if toolIndex < len(selectedSpools) else None

			if (selectedSpool != None):
				diameter = selectedSpool.diameter
				density = selectedSpool.density
				totalWeight = selectedSpool.totalWeight
				usedWeight = selectedSpool.usedWeight

				# need attributes present: diameter, density, totalWeight
				missing_fields = []
				if diameter is None:
					missing_fields.append('diameter')
				if density is None:
					missing_fields.append('density')
				if totalWeight is None:
					missing_fields.append('total weight')
				if usedWeight is None:
					usedWeight = 0.0

				if missing_fields:
					if (warnUser == True):
						self._sendMessageToClient(
							"warning", "Filament prediction not possible!",
							"Following fields not set in Spool '%s' (in tool %d): %s" % (selectedSpool.displayName, toolIndex, ', '.join(missing_fields))
						)
					someAttributesMissing = True
				else:
					not_a_number_fields = []
					try:
						diameter = float(diameter)
					except ValueError:
						not_a_number_fields.append('diameter')
					try:
						density = float(density)
					except ValueError:
						not_a_number_fields.append('density')
					try:
						totalWeight = float(totalWeight)
					except ValueError:
						not_a_number_fields.append('totalweight')
					try:
						usedWeight = float(usedWeight)
					except ValueError:
						not_a_number_fields.append('used weight')

					if not_a_number_fields:
						if (warnUser == True):
							self._sendMessageToClient(
								"warning", "Filament prediction not possible!",
								"One of the needed fields are not a number in Spool '%s' (in tool %d): %s" % (selectedSpool.displayName, toolIndex, ', '.join(not_a_number_fields))
							)
						someAttributesMissing = True
					else:
						# Benötigtes Gewicht = gewicht(geplante länge, durchmesser, dichte)
						requiredWeight = self._calculateWeight(filamentLength, diameter, density)

						# Vorhanden Gewicht = Gesamtgewicht - Verbrauchtes Gewicht
						# TODO don't calculate here use the value from the database
						remainingWeight = totalWeight - usedWeight

						saftyLengthInMM = self._settings.get_int([SettingsKeys.SETTINGS_KEY_SAFETY_LENGTH])
						if (saftyLengthInMM != 0):
							saftyRequiredWeight = self._calculateWeight(saftyLengthInMM, diameter, density)
							self._logger.info("saftyWeight '" + str(saftyRequiredWeight) + "' from saftyLengthInMM '" + str(saftyLengthInMM) + "' calculated")
							requiredWeight = requiredWeight + saftyRequiredWeight

						self._logger.info("tool" + str(toolIndex) + ", requiredWeight '" + str(requiredWeight) + "',  remainingWeight '" + str(remainingWeight) + "'")

						notEnough = False
						if remainingWeight < requiredWeight and requiredWeight > 0:
							self._logger.info("Filament not enough!")
							if (warnUser == True):
								self._sendMessageToClient(
									"warning", "Filament not enough!",
									"Required on tool %d: %dg, available from Spool '%s': '%dg'" % (toolIndex, requiredWeight, selectedSpool.displayName, remainingWeight)
								)
							notEnough = True
							overallNotEnough = True

						detailedSpoolResultItem = {
							"toolIndex": toolIndex,
							"requiredWeight": requiredWeight,
							"requiredLength": filamentLength,
							"remainingWeight": remainingWeight,
							"diameter": diameter,
							"density": density,
							"notEnough": notEnough,
							"spoolSelected": True,
							"spoolName": selectedSpool.displayName
						}
						requiredWeightResultDict["detailedSpoolResult"].append(detailedSpoolResultItem)
			else:
				# No selected spool for this tool-index, just create an simple entry
				detailedSpoolResultItem = {
					"toolIndex": toolIndex,
					"requiredLength": filamentLength,
					"spoolSelected": False,
					"spoolName": "not selected"
				}
				requiredWeightResultDict["detailedSpoolResult"].append(detailedSpoolResultItem)
				pass

		requiredWeightResultDict["attributesMissing"] = someAttributesMissing
		requiredWeightResultDict["notEnough"] = overallNotEnough

		return requiredWeightResultDict


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

		# self._filamentOdometer.reset()
		self.myFilamentOdometer.reset()

		reloadTable = False
		selectedSpools = self.loadSelectedSpools()
		self._readingFilamentMetaData()
		for toolIndex, filamentLength in enumerate(self.metaDataFilamentLengths):
			spoolModel = selectedSpools[toolIndex] if toolIndex < len(selectedSpools) else None

			if (spoolModel != None):
				if (StringUtils.isEmpty(spoolModel.firstUse) == True):
					firstUse = datetime.now()
					spoolModel.firstUse = firstUse
					self._databaseManager.saveSpool(spoolModel)
					reloadTable = True
		if reloadTable:
			self._sendDataToClient(dict(
										action="reloadTable"
										))
	# assign the current extrusion to the current selected spools

	def commitOdometerData(self):
		reload = False
		selectedSpools = self.loadSelectedSpools()
		for toolIndex, spoolModel in enumerate(selectedSpools):
			if spoolModel is None:
				self._logger.warning("Tool %d: No spool selected, could not update values after print" % toolIndex)
				continue

			# - Last usage datetime
			lastUsage = datetime.now()
			spoolModel.lastUse = lastUsage
			# - Used length
			try:
				allExtrusions = self.myFilamentOdometer.getExtrusionAmount()
				currentExtrusionLength = allExtrusions[toolIndex]
			except (KeyError, IndexError) as e:
				self._logger.info("Tool %d: No filament extruded" % toolIndex)
				continue
			self._logger.info("Tool %d: Extruded filament length: %s" % (toolIndex, str(currentExtrusionLength)))
			spoolUsedLength = 0.0 if StringUtils.isEmpty(spoolModel.usedLength) == True else spoolModel.usedLength
			self._logger.info("Tool %d: Current Spool used filament length: %s" % (toolIndex, str(spoolUsedLength)))
			newUsedLength = spoolUsedLength + currentExtrusionLength
			self._logger.info("Tool %d: New Spool used filament length: %s" % (toolIndex, str(newUsedLength)))
			spoolModel.usedLength = newUsedLength
			# - Used weight
			diameter = spoolModel.diameter
			density = spoolModel.density
			if diameter is None or density is None:
				self._logger.warning(
					"Tool %d: Could not update spool weight, because diameter or density not set in spool '%s'" % (toolIndex, spoolModel.displayName)
				)
			else:
				usedWeight = self._calculateWeight(currentExtrusionLength, diameter, density)
				spoolUsedWeight = 0.0 if spoolModel.usedWeight == None else spoolModel.usedWeight
				newUsedWeight = spoolUsedWeight + usedWeight
				spoolModel.usedWeight = newUsedWeight
				self._logger.info("Tool %d: spoolUsedWeight: %s" % (toolIndex, str(spoolUsedWeight)))
				self._logger.info("Tool %d: New spoolUsedWeight: %s" % (toolIndex, str(newUsedWeight)))

			self._databaseManager.saveSpool(spoolModel)

			eventPayload = {
				"toolId": toolIndex,
				"databaseId": spoolModel.databaseId,
				"spoolName": spoolModel.displayName,
				"material": spoolModel.material,
				"colorName": spoolModel.colorName,
				"remainingWeight": spoolModel.remainingWeight
			}
			self._sendPayload2EventBus(EventBusKeys.EVENT_BUS_SPOOL_WEIGHT_UPDATED_AFTER_PRINT, eventPayload)

			reload = True

		self.myFilamentOdometer.reset_extruded_length()

		if reload:
			self._sendDataToClient(dict(
				action="reloadTable and sidebarSpools"
			))

	#### print job finished
	def _on_printJobFinished(self, printStatus, payload):
		self.commitOdometerData()

		# update remaining data in selected spools after a print
		selectedSpools = self.loadSelectedSpools()
		requiredWeightResult = self._evaluateRequiredWeight(selectedSpools, None, False)
		requiredWeightResult["action"] = "requiredFilamentChanged"
		self._sendDataToClient(requiredWeightResult)

		if ("paused" != printStatus):
			self.clear_temp_offsets()

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
		# data for the sidebar
		self.checkRemainingFilament()
		pass

	def _on_clientClosed(self, payload):
		self.databaseConnectionProblemConfirmed = False

	def _on_file_selectionChanged(self, payload):
		self.checkRemainingFilament()
	pass


	######################################################################################### PUBLIC IMPLEMENTATION API
	def api_getSelectedSpoolInformations(self):
		"""
		Returns the current extruded filament for each tool
		:param string path:
		:return: array of spoolData-object ....
		"""
		spoolModels = self.loadSelectedSpools()
		result = []
		toolIndex = 0
		while toolIndex < len(spoolModels):
			spoolModel = spoolModels[toolIndex]
			spoolData = None
			if (spoolModel != None):
				spoolData = {
					"toolIndex": toolIndex,
					"databaseId": spoolModel.databaseId,
					"spoolName": spoolModel.displayName,
					"vendor": spoolModel.vendor,
					"material": spoolModel.material,
					"diameter": spoolModel.diameter,
					"density": spoolModel.density,
					"colorName": spoolModel.colorName,
					"color": spoolModel.color,
					"cost": spoolModel.cost,
					"weight": spoolModel.totalWeight
				}
			result.append(spoolData)

			toolIndex += 1
		return result

	def api_getExtrusionAmount(self):
		"""
		Returns the current extruded filament for each tool
		:param string path:
		:return: array of ....
		"""
		return self.myFilamentOdometer.getExtrusionAmount()
		pass


	######################################################################################### Hooks and public functions

	def on_after_startup(self):
		# check if needed plugins were available
		self._checkForMissingPluginInfos()
		pass

	# Listen to all  g-code which where already sent to the printer (thread: comm.sending_thread)
	def on_sentGCodeHook(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):

		# TODO maybe later via a queue
		# self._filamentOdometer.parse(gcode, cmd)
		self.myFilamentOdometer.processGCodeLine(cmd)
		# if self.pauseEnabled and self.check_threshold():
		# 	self._logger.info("Filament is running out, pausing print")
		# 	self._printer.pause_print()
		pass

	def on_event(self, event, payload):

		# if (event != "RegisteredMessageReceived"):
		# 	print("*** EVENT: " + event)
		#
		# if ("plugin_spoolmanager" in event):
		# 	print(payload)
		# 	pass

		if (Events.CLIENT_OPENED == event):
			self._on_clientOpened(payload)
			return
		if (Events.CLIENT_CLOSED == event):
			self._on_clientClosed(payload)
			return

		elif (Events.PRINT_STARTED == event):
			self.alreadyCanceled = False
			self._on_printJobStarted()

		elif (Events.PRINT_PAUSED == event):
			self._on_printJobFinished("paused", payload)

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
		# Enable cleaning up any offsets that are turned off
		oldToolOffsetEnabled = self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_TOOL_OFFSET_ENABLED])
		oldBedOffsetEnabled = self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_BED_OFFSET_ENABLED])
		oldEnclosureOffsetEnabled = self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_ENCLOSURE_OFFSET_ENABLED])

		# # default save function
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

		# Clean up any offsets that are turned off
		newToolOffsetEnabled = self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_TOOL_OFFSET_ENABLED])
		newBedOffsetEnabled = self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_BED_OFFSET_ENABLED])
		newEnclosureOffsetEnabled = self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_ENCLOSURE_OFFSET_ENABLED])

		offsetCleanup = False
		offset_dict = dict()
		if newToolOffsetEnabled == False and oldToolOffsetEnabled == True:
			offsetCleanup = True
			offset_dict["tool0"] = 0
		if newBedOffsetEnabled == False and oldBedOffsetEnabled == True:
			offsetCleanup = True
			offset_dict["bed"] = 0
		if newEnclosureOffsetEnabled == False and oldEnclosureOffsetEnabled == True:
			offsetCleanup = True
			offset_dict["chamber"] = 0

		if offsetCleanup :
			self._printer.set_temperature_offset(offset_dict)

		# Update Temperature Offsets
		selectedSpools = self.loadSelectedSpools()
		self._readingFilamentMetaData()
		for toolIndex, filamentLength in enumerate(self.metaDataFilamentLengths):
			selectedSpool = selectedSpools[toolIndex] if toolIndex < len(selectedSpools) else None
			if (selectedSpool != None):
				self.set_temp_offsets(toolIndex, selectedSpool)

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

		settings = dict(
			installed_version=self._plugin_version
		)

		# Not visible
		settings[SettingsKeys.SETTINGS_KEY_SELECTED_SPOOLS_DATABASE_IDS] = []
		settings[SettingsKeys.SETTINGS_KEY_HIDE_EMPTY_SPOOL_IN_SIDEBAR] = False
		settings[SettingsKeys.SETTINGS_KEY_HIDE_INACTIVE_SPOOL_IN_SIDEBAR] = True
		## Genral
		settings[SettingsKeys.SETTINGS_KEY_REMINDER_SELECTING_SPOOL] = True
		settings[SettingsKeys.SETTINGS_KEY_WARN_IF_SPOOL_NOT_SELECTED] = True
		settings[SettingsKeys.SETTINGS_KEY_WARN_IF_FILAMENT_NOT_ENOUGH] = True
		settings[SettingsKeys.SETTINGS_KEY_CURRENCY_SYMBOL] = "€"
		settings[SettingsKeys.SETTINGS_KEY_SAFETY_LENGTH] = 0

		## QR-Code
		settings[SettingsKeys.SETTINGS_KEY_QR_CODE_ENABLED] = True
		settings[SettingsKeys.SETTINGS_KEY_QR_CODE_USE_URL_PREFIX] = False
		settings[SettingsKeys.SETTINGS_KEY_QR_CODE_URL_PREFIX] = None
		settings[SettingsKeys.SETTINGS_KEY_QR_CODE_FILL_COLOR] = "#008000"
		settings[SettingsKeys.SETTINGS_KEY_QR_CODE_BACKGROUND_COLOR] = "#ffffff"
		settings[SettingsKeys.SETTINGS_KEY_QR_CODE_WIDTH] = "100"
		settings[SettingsKeys.SETTINGS_KEY_QR_CODE_HEIGHT] = "100"

		## Export / Import
		settings[SettingsKeys.SETTINGS_KEY_IMPORT_CSV_MODE] = SettingsKeys.KEY_IMPORTCSV_MODE_APPEND

		## Temperature
		settings[SettingsKeys.SETTINGS_KEY_TOOL_OFFSET_ENABLED] = False
		settings[SettingsKeys.SETTINGS_KEY_BED_OFFSET_ENABLED] = False
		settings[SettingsKeys.SETTINGS_KEY_ENCLOSURE_OFFSET_ENABLED] = False

		## Debugging
		settings[SettingsKeys.SETTINGS_KEY_SQL_LOGGING_ENABLED] = False
		settings[SettingsKeys.SETTINGS_KEY_EXTRUSION_DEBUGGING_ENABLED] = False

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

		settings["excludedFromTemplateCopy"] = []
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
				# "js/jquery.datetimepicker.full.min.js",
				"js/jquery.datetimepicker.full.js",
				"js/tinycolor.js",
				"js/pick-a-color.js",
				"js/ResetSettingsUtilV3.js",
				"js/ComponentFactory.js",
				"js/TableItemHelper.js",
				"js/SpoolManager.js",
				"js/SpoolManager-APIClient.js",
				"js/SpoolManager-FilterSorter.js",
				"js/SpoolManager-SpoolSelectionTableComp.js",
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

				# Release channels
				stable_branch=dict(
					name="Only Release",
					branch="master",
					comittish=["master"]
				),
				prerelease_branches=[
					dict(
						name="Release & Candidate",
						branch="pre-release",
						comittish=["pre-release", "master"],
					),
					dict(
						name="Release & Candidate & under Development",
						branch="development",
						comittish=["development", "pre-release", "master"],
					)
				],

				# update method: pip
				pip="https://github.com/OllisGit/OctoPrint-SpoolManager/releases/download/{target_version}/master.zip"
			)
		)

	def register_custom_events(*args, **kwargs):
		return [EventBusKeys.EVENT_BUS_SPOOL_WEIGHT_UPDATED_AFTER_PRINT,
				EventBusKeys.EVENT_BUS_SPOOL_SELECTED,
				EventBusKeys.EVENT_BUS_SPOOL_DESELECTED,
				EventBusKeys.EVENT_BUS_SPOOL_ADDED,
				EventBusKeys.EVENT_BUS_SPOOL_DELETED
				]



	# def message_on_connect(self, comm, script_type, script_name, *args, **kwargs):
	# 	print(script_name)
	# 	if not script_type == "gcode" or not script_name == "afterPrinterConnected":
	# 		return None
	#
	# 	prefix = None
	# 	postfix = "M117 OctoPrint connected"
	# 	variables = dict(myvariable="Hi! I'm a variable!")
	# 	return prefix, postfix, variables

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
		# "octoprint.comm.protocol.scripts": __plugin_implementation__.message_on_connect
		"octoprint.events.register_custom_events":  __plugin_implementation__.register_custom_events
	}

