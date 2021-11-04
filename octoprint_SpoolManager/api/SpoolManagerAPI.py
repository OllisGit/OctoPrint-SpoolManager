# coding=utf-8
from __future__ import absolute_import

import logging

import octoprint.plugin
import datetime
import flask
from flask import jsonify, request, make_response, Response, send_file, abort
import json
import shutil
import tempfile
import threading
import qrcode
from io import BytesIO     # for handling byte strings
from math import pi as PI

from octoprint_SpoolManager import DatabaseManager
from octoprint_SpoolManager.models.SpoolModel import SpoolModel
from octoprint_SpoolManager.common import StringUtils, CSVExportImporter
from octoprint_SpoolManager.api import Transformer
from octoprint_SpoolManager.common.SettingsKeys import SettingsKeys

class SpoolManagerAPI(octoprint.plugin.BlueprintPlugin):

	def _sendCSVUploadStatusToClient(self, importStatus, currenLineNumber, backupFilePath,  successMessages, errorCollection):

		self._sendDataToClient(dict(action="csvImportStatus",
									importStatus = importStatus,
									currenLineNumber = currenLineNumber,
									backupFilePath = backupFilePath,
									successMessages=successMessages,
									errorCollection = errorCollection
									)
							   )

	def _updateSpoolModelFromJSONData(self, spoolModel, jsonData):

		spoolModel.version = self._toIntFromJSONOrNone("version", jsonData)
		# if statement is needed because assigning None is alos detected as an dirtyField
		if (self._getValueFromJSONOrNone("databaseId", jsonData) != None):
			spoolModel.databaseId = self._getValueFromJSONOrNone("databaseId", jsonData)

		spoolModel.isTemplate = self._getValueFromJSONOrNone("isTemplate", jsonData)
		spoolModel.isActive = self._getValueFromJSONOrNone("isActive", jsonData)
		spoolModel.displayName = self._getValueFromJSONOrNone("displayName", jsonData)
		spoolModel.vendor = self._getValueFromJSONOrNone("vendor", jsonData)
		spoolModel.material = self._getValueFromJSONOrNone("material", jsonData)
		spoolModel.density = self._toFloatFromJSONOrNone("density", jsonData)
		spoolModel.diameter = self._toFloatFromJSONOrNone("diameter", jsonData)
		spoolModel.diameterTolerance = self._toFloatFromJSONOrNone("diameterTolerance", jsonData)
		spoolModel.colorName = self._getValueFromJSONOrNone("colorName", jsonData)
		spoolModel.color = self._getValueFromJSONOrNone("color", jsonData)
		spoolModel.flowRateCompensation = self._toIntFromJSONOrNone("flowRateCompensation", jsonData)
		spoolModel.temperature = self._toIntFromJSONOrNone("temperature", jsonData)
		spoolModel.bedTemperature = self._toIntFromJSONOrNone("bedTemperature", jsonData)
		spoolModel.enclosureTemperature = self._toIntFromJSONOrNone("enclosureTemperature", jsonData)
		spoolModel.offsetTemperature = self._toIntFromJSONOrNone("offsetTemperature", jsonData)
		spoolModel.offsetBedTemperature = self._toIntFromJSONOrNone("offsetBedTemperature", jsonData)
		spoolModel.offsetEnclosureTemperature = self._toIntFromJSONOrNone("offsetEnclosureTemperature", jsonData)
		spoolModel.totalWeight = self._toFloatFromJSONOrNone("totalWeight", jsonData)
		spoolModel.spoolWeight = self._toFloatFromJSONOrNone("spoolWeight", jsonData)
		spoolModel.remainingWeight = self._toFloatFromJSONOrNone("remainingWeight", jsonData)
		spoolModel.totalLength = self._toIntFromJSONOrNone("totalLength", jsonData)
		spoolModel.usedLength = self._toIntFromJSONOrNone("usedLength", jsonData)
		spoolModel.usedWeight = self._toFloatFromJSONOrNone("usedWeight", jsonData)
		spoolModel.code = self._getValueFromJSONOrNone("code", jsonData)

		spoolModel.firstUse = StringUtils.transformToDateTimeOrNone(self._getValueFromJSONOrNone("firstUse", jsonData))
		spoolModel.lastUse = StringUtils.transformToDateTimeOrNone(self._getValueFromJSONOrNone("lastUse", jsonData))
		spoolModel.purchasedOn = StringUtils.transformToDateTimeOrNone(self._getValueFromJSONOrNone("purchasedOn", jsonData))

		spoolModel.purchasedFrom = self._getValueFromJSONOrNone("purchasedFrom", jsonData)
		spoolModel.cost = self._toFloatFromJSONOrNone("cost", jsonData)
		spoolModel.costUnit = self._getValueFromJSONOrNone("costUnit", jsonData)

		spoolModel.labels = json.dumps(self._getValueFromJSONOrNone("labels", jsonData))

		spoolModel.noteText = self._getValueFromJSONOrNone("noteText", jsonData)
		spoolModel.noteDeltaFormat = json.dumps(self._getValueFromJSONOrNone("noteDeltaFormat", jsonData))
		spoolModel.noteHtml = self._getValueFromJSONOrNone("noteHtml", jsonData)
		pass


	def _getValueFromJSONOrNone(self, key, json):
		if key in json:
			return json[key]
		return None

	def _toFloatFromJSONOrNone(self, key, json):
		value = self._getValueFromJSONOrNone(key, json)
		if (value != None):
			if (StringUtils.isNotEmpty(value)):
				try:
					value = float(value)
				except Exception as e:
					errorMessage = str(e)
					self._logger.error("could not transform value '"+str(value)+"' for key '"+key+"' to float:" + errorMessage)
					value = None
			else:
				value = None
		return value

	def _toIntFromJSONOrNone(self, key, json):
		value = self._getValueFromJSONOrNone(key, json)
		if (value != None):
			if (StringUtils.isNotEmpty(value)):
				try:
					value = int(value)
				except Exception as e:
					errorMessage = str(e)
					self._logger.error("could not transform value '"+str(value)+"' for key '"+key+"' to int:" + errorMessage)
					value = None
			else:
				value = None
		return value

	# def _formatDateOrNone(self, dateValue):
	# 	if dateValue != None:
	# 		return dateValue.strftime('%d.%m.%Y %H:%M')
	# 	return None
	# def _formatDateOrNone(self, dateValue):
	# 	if dateValue != None:
	# 		return datetime.strptime(str(dateValue), '%d.%m.%Y %H:%M')
	# 	return None

	def loadSelectedSpools(self):
		spoolModelList = []
		databaseIds = self._settings.get([SettingsKeys.SETTINGS_KEY_SELECTED_SPOOLS_DATABASE_IDS])

		for i, databaseId in enumerate(databaseIds):
			spoolModel = None
			if (databaseId != None):
				self._databaseManager.connectoToDatabase()
				spoolModel = self._databaseManager.loadSpool(databaseId)
				self._databaseManager.closeDatabase()
				if (spoolModel == None):
					self._logger.warning(
						"Last selected Spool for Tool %d from plugin-settings not found in database. Maybe deleted in the meantime." % i)
			spoolModelList.append(spoolModel)

		return spoolModelList

	def _createSpoolModelFromLegacy(self, allSpoolLegacyList):
		allSpoolModels = list()
		for spoolDict in allSpoolLegacyList:
			spoolModel = SpoolModel()

			spoolIdInt = spoolDict["id"]
			nameUnicode = spoolDict["name"]
			usedWeightFloat = spoolDict["used"]
			totalWeightFloat = spoolDict["weight"]
			tempOffsetInt = spoolDict["temp_offset"]
			costFloat = spoolDict["cost"]
			profileDict = spoolDict["profile"]
			profileIdInt = profileDict["id"]
			diameterFloat = profileDict["diameter"]
			materialUnicode = profileDict["material"]
			vendorUnicode = profileDict["vendor"]
			densityFloat = profileDict["density"]

			spoolModel.displayName = nameUnicode
			spoolModel.vendor = vendorUnicode

			spoolModel.material = materialUnicode
			spoolModel.density = densityFloat
			spoolModel.diameter = diameterFloat
			spoolModel.cost = costFloat
			spoolModel.costUnit = self._filamentManagerPluginImplementation._settings.get(["currencySymbol"])
			spoolModel.totalWeight = totalWeightFloat
			spoolModel.usedWeight = usedWeightFloat

			spoolModel.usedLength = self._calculateUsedLength(spoolModel.usedWeight, spoolModel.density, spoolModel.diameter)

			allSpoolModels.append(spoolModel)

		return allSpoolModels

	def _calculateUsedLength(self, usedWeight, density, diameter):
		if (diameter == None or density == None or usedWeight == None):
			self._logger.info("Could not calculate used length because some values (usedWeigth, density, diameter) were missing")
			return None
		radius = diameter / 2.0
		volume = (usedWeight) / density
		length = (volume * 1000) / PI * radius * radius
		lengthRounded = int(round(length))
		return lengthRounded;

	def _resetSelectedSpools(self):
		self._settings.set([SettingsKeys.SETTINGS_KEY_SELECTED_SPOOLS_DATABASE_IDS], [])
		self._settings.save()

	def _selectSpool(self, toolIndex, databaseId):
		# three cases
		#  1. databaseId != -1 toolIndex != -1	select spool for toool 	||
		#  2. databaseId == -1 toolIndex !=	-1	remove spool from tool	|
		#  3. databaseId != -1 toolIndex == -1	remove tool from spool 	||

		databaseIds = self._settings.get([SettingsKeys.SETTINGS_KEY_SELECTED_SPOOLS_DATABASE_IDS])

		spoolModel = None
		if (databaseId != -1):
			spoolModel = self._databaseManager.loadSpool(databaseId)
			if (spoolModel != None):
				self._logger.info(
					"Store selected spool %s for tool %d in settings." %
					(spoolModel.displayName, toolIndex)
				)
				# assign model to selected toolId
				if (toolIndex != -1):
					databaseIds = databaseIds + [None] * (toolIndex + 1 - len(databaseIds))  # pad list to the needed length
					databaseIds = [(None if i == databaseId else i) for i in databaseIds] # remove spool from other tool(s)
					databaseIds[toolIndex] = databaseId
				else:
					# spool present, but no toolId -> remove spool from current toolIndex
					i = 0
					while i < len(databaseIds):
						if (databaseIds[i] == databaseId):
							databaseIds[i] = None
							break
						i += 1
					pass
			else:
				self._logger.warning(
					"Selected Spool with id %d for tool %d not in database anymore. Maybe deleted in the meantime." %
					(databaseId, toolIndex)
				)
				# remove spool from current toolIndex
				i = 0
				while i < len(databaseIds):
					if (databaseIds[i] == databaseId):
						databaseIds[i] = None
		else:
			if (toolIndex == -1):
				self._logger.warn("databaseId and toolId is -1. This should not happen, strange!!!")
				return None

			# remove current spool from toolIndex
			if (toolIndex < len(databaseIds)):
				databaseIds[toolIndex] = None

		self._settings.set([SettingsKeys.SETTINGS_KEY_SELECTED_SPOOLS_DATABASE_IDS], databaseIds)
		self._settings.save()

		# only check filament for the spool that was changed, as to not spam the user with warnings (for a specific toolIndex)
		if spoolModel is not None and toolIndex != -1:
			self.checkRemainingFilament(toolIndex)

		return spoolModel

	################################################### APIs

	@octoprint.plugin.BlueprintPlugin.route("/sampleCSV", methods=["GET"])
	def sampleCSV(self):

		allSpoolModels = list()

		spoolModel = CSVExportImporter.createSampleSpoolModel()
		allSpoolModels.append(spoolModel)
		return Response(CSVExportImporter.transform2CSV(allSpoolModels),
						mimetype='text/csv',
						headers={'Content-Disposition': 'attachment; filename=SpoolManager-SAMPLE.csv'})

	##############################################################################################   ALLOWED TO PRINT
	@octoprint.plugin.BlueprintPlugin.route("/allowedToPrint", methods=["GET"])
	def allowed_to_print(self):

		checkForSelectedSpool = self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_WARN_IF_SPOOL_NOT_SELECTED])
		checkForFilamentLength = self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_WARN_IF_FILAMENT_NOT_ENOUGH])
		reminderSelectingSpool = self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_REMINDER_SELECTING_SPOOL])

		spoolModels = self.loadSelectedSpools()
		metaOrAttributesMissing = False
		result = {
			'noSpoolSelected': [],
			'filamentNotEnough': [],
			'reminderSpoolSelection': [],
		}

		filamentLengthPresentInMeta = self._readingFilamentMetaData()
		printer_profile = self._printer_profile_manager.get_current_or_default()
		printerProfileToolCount = printer_profile['extruder']['count']
		# for toolIndex, filamentLength in enumerate(self.metaDataFilamentLengths):
		for toolIndex in range(printerProfileToolCount):
			# we go over the filamentlength because those are what matters for this print
			if filamentLengthPresentInMeta:
				if toolIndex >= len(self.metaDataFilamentLengths):
					# if this tool is not used (no filaLenght) in this print, everything is fine
					continue

			spoolModel = spoolModels[toolIndex] if toolIndex < len(spoolModels) else None

			infoData = {
				"toolIndex": toolIndex,
				"spoolName": spoolModel.displayName if spoolModel else '(no spool selected)',
				"material": spoolModel.material if spoolModel else '',
				"remainingWeight": spoolModel.remainingWeight if spoolModel else '',
				"toolOffset": spoolModel.offsetTemperature if spoolModel else '',
				"bedOffset": spoolModel.offsetBedTemperature if spoolModel else '',
				"enclosureOffset": spoolModel.offsetEnclosureTemperature if spoolModel else ''
			}

			requiredWeightResult = self.checkRemainingFilament(toolIndex)
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
			if (requiredWeightResult["metaDataMissing"] == True or requiredWeightResult["attributesMissing"] == True):
				metaOrAttributesMissing = True

			detailedSpoolResult = None
			if ("detailedSpoolResult" in requiredWeightResult and len(requiredWeightResult["detailedSpoolResult"]) > 0):
				detailedSpoolResult = requiredWeightResult["detailedSpoolResult"][0]

			if spoolModel is not None and detailedSpoolResult is not None and detailedSpoolResult["spoolSelected"] == True:

				if (detailedSpoolResult["requiredLength"] > 0):
					if (detailedSpoolResult["notEnough"] == True):
						# if not enough or needed amount could not calculated
						result['filamentNotEnough'].append(infoData)
					# add every spool for reminding, if more the 0gr is needed
					result['reminderSpoolSelection'].append(infoData)
			elif checkForSelectedSpool:
				if (detailedSpoolResult is not None):
					if (detailedSpoolResult["requiredLength"] > 0):
						result['noSpoolSelected'].append(infoData)
				else:
					result['noSpoolSelected'].append(infoData)

			# 	if (metaNotPresent or
			# 		attributesMissing or
			# 		notEnough
			# 	):
			# 		# if not enough or needed amount could not calculated
			# 		result['filamentNotEnough'].append(infoData)
			# 		if (metaNotPresent or
			# 			attributesMissing):
			# 			metaOrAttributesMissing = True
			#
			# 	# add every spool for reminding
			# 	result['reminderSpoolSelection'].append(infoData)
			# elif checkForSelectedSpool:
			# 	# if no metatdata is present we cant check if this tool is needed, so we cant inform the user that a selection is missing
			# 	if (filamentLengthPresentInMeta == True):
			# 		result['noSpoolSelected'].append(infoData)

		# check if the user want a popup
		if (checkForFilamentLength == False):
			result['filamentNotEnough'] = []

		if (reminderSelectingSpool == False):
			# no popup, because turned off by user
			result['reminderSpoolSelection'] = []

		return flask.jsonify({
			"result": result,
			"metaOrAttributesMissing": metaOrAttributesMissing,
			"toolOffsetEnabled": self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_TOOL_OFFSET_ENABLED]),
			"bedOffsetEnabled": self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_BED_OFFSET_ENABLED]),
			"enclosureOffsetEnabled": self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_ENCLOSURE_OFFSET_ENABLED]),
		})

	#####################################################################################################   SELECT SPOOL
	@octoprint.plugin.BlueprintPlugin.route("/selectSpool", methods=["PUT"])
	def select_spool(self):
		jsonData = request.json

		databaseId = self._toIntFromJSONOrNone("databaseId", jsonData)
		toolIndex = self._toIntFromJSONOrNone("toolIndex", jsonData)

		if self._printer.is_printing():
			# changing a spool mid-print? we want to know
			commitCurrentSpoolValues = self._getValueFromJSONOrNone("commitCurrentSpoolValues", jsonData)
			if commitCurrentSpoolValues is None:
				self._logger.warning("selectSpool endpoint called mid-print without commitCurrentState parameter - this shouldn't happen")
				abort(409)

			if commitCurrentSpoolValues:
				self._logger.info("commitCurrentSpoolValues == True")
				self.commitOdometerData()

		spoolModel = self._selectSpool(toolIndex, databaseId)

		spoolModelAsDict = None
		if (spoolModel != None):
			spoolModelAsDict = Transformer.transformSpoolModelToDict(spoolModel)

		try:
			self.set_temp_offsets(toolIndex, spoolModel)
		except Exception as e:
			self._sendMessageToClient("warning", "Temperature offsets failed to set!", str(e))

		self.checkRemainingFilament()

		return flask.jsonify({
								"selectedSpool": spoolModelAsDict
							})

	#####################################################################################################   SELECT SPOOL BY QR
	@octoprint.plugin.BlueprintPlugin.route("/selectSpoolByQRCode/<int:databaseId>", methods=["GET"])
	def selectSpoolByQRCode(self, databaseId):
		self._logger.info("API select spool by QR code" + str(databaseId))

		if self._printer.is_printing():
			# not doing this mid-print since we can't ask the user what to do
			abort(409)
			return

		# TODO QR-Code pre-select always tool0 and then the edit-dialog is shown. Better approach: show dialog and the user could choose
		spoolModel = self._selectSpool(0, databaseId)

		spoolModelAsDict = None
		if (spoolModel != None):
			spoolModelAsDict = Transformer.transformSpoolModelToDict(spoolModel)
			#Take us back to the SpoolManager plugin tab
			redirectURLWithSpoolSelection = flask.url_for("index", _external=True)+"#tab_plugin_SpoolManager-spoolId"+str(databaseId)
			return flask.redirect(redirectURLWithSpoolSelection,307)
		else:
			abort(404)

	# hmmm..TODO not fully tested
	def is_blueprint_protected(self):
		return False  # No API key required to request API access

	#####################################################################################################   GENERATE QR FOR SPOOL
	@octoprint.plugin.BlueprintPlugin.route("/generateQRCode/<int:databaseId>", methods=["GET"])
	def generateSpoolQRCode(self, databaseId):
		if (self._databaseManager.loadSpool(databaseId) is not None):
			self._logger.info("API generate QR code for Spool")

			# windowLocation = request.args.get("windowlocation")

			from PIL import Image
			imageFileLocation = self._basefolder + "/static/images/SPMByOlli.png"
			olliImage = Image.open(imageFileLocation)#.crop((175, 90, 235, 150))


			# https://note.nkmk.me/en/python-pillow-qrcode/
			qrMaker = qrcode.QRCode(
				border=4,
				error_correction=qrcode.constants.ERROR_CORRECT_H
			)

			# spoolSelectionUrl = flask.url_for("plugin.SpoolManager.selectSpoolByQRCode", _external=True, _scheme="https", databaseId=databaseId)
			spoolSelectionUrl = flask.url_for("plugin.SpoolManager.selectSpoolByQRCode", _external=True, databaseId=databaseId)
			qrMaker.add_data(spoolSelectionUrl)
			qrMaker.make(fit=True, )

			fillColor = self._settings.get([SettingsKeys.SETTINGS_KEY_QR_CODE_FILL_COLOR])
			backgroundColor = self._settings.get([SettingsKeys.SETTINGS_KEY_QR_CODE_BACKGROUND_COLOR])

			img_qr_big = qrMaker.make_image(fill_color=fillColor, back_color=backgroundColor).convert('RGB')
			pos = ((img_qr_big.size[0] - olliImage.size[0]) // 2, (img_qr_big.size[1] - olliImage.size[1]) // 2)
			img_qr_big.paste(olliImage, pos)
			# img_qr_big.save('data/dst/qr_lena2.png')
			#
			#
			#
			# # qrImage = qrMaker.make_image(fill_color="darkgreen", back_color="white")
			# qrImage = qrMaker.make_image(fill_color=fillColor, back_color=backgroundColor)

			qr_io = BytesIO()
			# qrImage.save(qr_io, 'JPEG', quality=100)
			img_qr_big.save(qr_io, 'JPEG', quality=100)
			qr_io.seek(0)

			return send_file(qr_io, mimetype='image/jpeg')
		else:
			abort(404)

	######################################################################################   UPLOAD CSV FILE (in Thread)

	@octoprint.plugin.BlueprintPlugin.route("/importCSV", methods=["POST"])
	def importSpoolData(self):

		input_name = "file"
		input_upload_path = input_name + "." + self._settings.global_get(["server", "uploads", "pathSuffix"])

		if input_upload_path in flask.request.values:

			importMode = flask.request.form["importCSVMode"]
			# file was uploaded
			sourceLocation = flask.request.values[input_upload_path]

			# because we process in seperate thread we need to create our own temp file, the uploaded temp file will be deleted after this request-call
			archive = tempfile.NamedTemporaryFile(delete=False)
			archive.close()
			shutil.copy(sourceLocation, archive.name)
			sourceLocation = archive.name


			thread = threading.Thread(target=self._processCSVUploadAsync,
									  args=(sourceLocation,
											importMode,
											self._databaseManager,
											self._sendCSVUploadStatusToClient,
											self._logger))
			thread.daemon = True
			thread.start()

			# targetLocation = self._cameraManager.buildSnapshotFilenameLocation(snapshotFilename, False)
			# os.rename(sourceLocation, targetLocation)
			pass
		else:
			return flask.make_response("Invalid request, neither a file nor a path of a file to restore provided", 400)


		return flask.jsonify(started=True)


	def _processCSVUploadAsync(self, path, importCSVMode, databaseManager, sendCSVUploadStatusToClient, logger):
		errorCollection = list()

		# - parsing
		# - backup
		# - append or replace

		def updateParsingStatus(lineNumber):
			# importStatus, currenLineNumber, backupFilePath,  successMessages, errorCollection
			sendCSVUploadStatusToClient("running", lineNumber, "", "", errorCollection)

		resultOfSpools = CSVExportImporter.parseCSV(path, updateParsingStatus, errorCollection, logger)

		if (len(errorCollection) != 0):
			successMessage = "Some error(s) occurs during parsing! No spools imported!"
			# importStatus, currenLineNumber, backupFilePath,  successMessages, errorCollection
			sendCSVUploadStatusToClient("finished", "", "", successMessage, errorCollection)
			return

		importModeText = "append"
		backupDatabaseFilePath = None
		if (len(resultOfSpools) > 0):
			# we could import some jobs

			# - backup
			backupDatabaseFilePath = databaseManager.backupDatabaseFile()

			# - import mode append/replace
			if (SettingsKeys.KEY_IMPORTCSV_MODE_REPLACE == importCSVMode):
				# delete old database and init a clean database
				databaseManager.reCreateDatabase()
				# reset selected spool
				self._resetSelectedSpools()

				importModeText = "fully replaced"

			# - insert all printjobs in database
			currentSpoolNumber = 0
			for spool in resultOfSpools:
				currentSpoolNumber = currentSpoolNumber + 1
				updateParsingStatus(currentSpoolNumber)

				remainingWeight = Transformer.calculateRemainingWeight(spool.usedWeight, spool.totalWeight)
				if (remainingWeight != None):
					spool.remainingWeight = remainingWeight
					# spool.save()

				spool.isActive = True

				databaseManager.saveSpool(spool)
			pass
		else:
			errorCollection.append("Nothing to import!")

		successMessage = ""
		if (len(errorCollection) == 0):
			successMessage = "All data is successful " + importModeText + " with '" + str(len(resultOfSpools)) + "' spools."
		else:
			successMessage = "Some error(s) occurs! Maybe you need to manually rollback the database!"
		logger.info(successMessage)
		sendCSVUploadStatusToClient("finished", "", backupDatabaseFilePath,  successMessage, errorCollection)
		pass

	def _buildDatabaseSettingsFromJson(self, jsonData):

		databaseSettings = DatabaseManager.DatabaseSettings()
		databaseSettings.useExternal =  self._getValueFromJSONOrNone(SettingsKeys.SETTINGS_KEY_DATABASE_USE_EXTERNAL, jsonData)
		databaseSettings.type =  self._getValueFromJSONOrNone(SettingsKeys.SETTINGS_KEY_DATABASE_TYPE, jsonData)
		databaseSettings.host =  self._getValueFromJSONOrNone(SettingsKeys.SETTINGS_KEY_DATABASE_HOST, jsonData)
		databaseSettings.port =  self._getValueFromJSONOrNone(SettingsKeys.SETTINGS_KEY_DATABASE_PORT, jsonData)
		databaseSettings.name =  self._getValueFromJSONOrNone(SettingsKeys.SETTINGS_KEY_DATABASE_NAME, jsonData)
		databaseSettings.user =  self._getValueFromJSONOrNone(SettingsKeys.SETTINGS_KEY_DATABASE_USER, jsonData)
		databaseSettings.password =  self._getValueFromJSONOrNone(SettingsKeys.SETTINGS_KEY_DATABASE_PASSWORD, jsonData)

		return databaseSettings


	#######################################################################################   DOWNLOAD DATABASE-FILE
	@octoprint.plugin.BlueprintPlugin.route("/downloadDatabase", methods=["GET"])
	def downloadDatabase(self):
		return send_file(self._databaseManager.getDatabaseSettings().fileLocation,
						 mimetype='application/octet-stream',
						 attachment_filename='spoolmanager.db',
						 as_attachment=True)


	#######################################################################################   DELETE DATABASE
	@octoprint.plugin.BlueprintPlugin.route("/deleteDatabase/<string:databaseType>", methods=["POST"])
	def deleteDatabase(self, databaseType):

		databaseSettings = None
		if (databaseType == "external"):
			jsonData = request.json
			databaseSettings = self._buildDatabaseSettingsFromJson(jsonData)

		self._databaseManager.reCreateDatabase(databaseSettings)

		return flask.jsonify({
			"result": "success"
		})



	#######################################################################################   LOAD DATABASE METADATA
	@octoprint.plugin.BlueprintPlugin.route("/loadDatabaseMetaData", methods=["GET"])
	def loadDatabaseMetaData(self):

		# databaseId = self._getValueFromJSONOrNone("databaseId", jsonData)
		metaDataResult = self._databaseManager.loadDatabaseMetaInformations(None)

		return flask.jsonify({
			"metadata": metaDataResult
		})

	#######################################################################################   TEST DATABASE CONNECTION
	@octoprint.plugin.BlueprintPlugin.route("/testDatabaseConnection", methods=["PUT"])
	def testDatabaseConnection(self):

		jsonData = request.json

		databaseSettings = self._buildDatabaseSettingsFromJson(jsonData)

		# databaseId = self._getValueFromJSONOrNone("databaseId", jsonData)
		metaDataResult = self._databaseManager.loadDatabaseMetaInformations(databaseSettings)

		return flask.jsonify({
			"metadata": metaDataResult
		})

	###############################################################################  CONFIRM DATABASE CONNECTION PROBLEM
	@octoprint.plugin.BlueprintPlugin.route("/confirmDatabaseProblemMessage", methods=["PUT"])
	def confirmDatabaseConnectionProblem(self):

		self.databaseConnectionProblemConfirmed = True

		# return flask.jsonify({
		# 	"metadata": metaDataResult
		# })
		return flask.jsonify()

	###########################################################################################   EXPORT DATABASE as CSV
	@octoprint.plugin.BlueprintPlugin.route("/exportSpools/<string:exportType>", methods=["GET"])
	def exportSpoolsData(self, exportType):

		if exportType == "CSV":
			allSpoolModels = self._databaseManager.loadAllSpoolsByQuery(None)

			now = datetime.datetime.now()
			currentDate = now.strftime("%Y%m%d-%H%M")
			fileName = "SpoolManager-" + currentDate + ".csv"

			return Response(CSVExportImporter.transform2CSV(allSpoolModels),
							mimetype='text/csv',
							headers={'Content-Disposition': 'attachment; filename=' + fileName})

		else:
			if (exportType == "legacyFilamentManager"):
				allSpoolLegacyList = self._filamentManagerPluginImplementation.filamentManager.get_all_spools()
				if (allSpoolLegacyList != None):

					allSpoolModelList = self._createSpoolModelFromLegacy(allSpoolLegacyList)

					now = datetime.datetime.now()
					currentDate = now.strftime("%Y%m%d-%H%M")
					fileName = "FilamentManager-" + currentDate + ".csv"

					return Response(CSVExportImporter.transform2CSV(allSpoolModelList),
									mimetype='text/csv',
									headers={'Content-Disposition': 'attachment; filename='+fileName})

				pass

			print("BOOOMM not supported type")
		pass



	##################################################################################################   LOAD ALL SPOOLS
	@octoprint.plugin.BlueprintPlugin.route("/loadSpoolsByQuery", methods=["GET"])
	def loadAllSpoolsByQuery(self):

		self._logger.debug("API Load all spool")
		# sp1 = SpoolModel()
		# sp1.displayName = "Spool No.1"
		# sp1.vendor = "Janbex"
		# sp1.material = "ABS"
		# sp1.color = "#00dd00"
		# sp1.density = 123.23
		# sp1.diameter = 432.12
		# sp1.temperature = 221
		# sp1.firstUse = datetime.datetime(2019, 5, 17)
		# sp1.lastUse = datetime.datetime(2019, 6, 4)
		# sp1.remainingWeight = 1234
		# sp1.weight = 2000
		# sp1.usedPercentage = str(1234.0 / (2000.0 / 100.0))
		# sp1.usedLength = 32
		# sp1.code = "XS-28787-HKH-234"
		# sp1.purchasedOn = datetime.datetime(2018, 4, 3)
		# sp1.purchasedFrom = "http://www.amazon.de/eorjoeiirjfoiejfoijeroffjeroeoidj"
		# sp1.cost = 3.14
		#
		# sp2 = SpoolModel()
		# sp2.displayName = "Spool No.2"
		# sp2.vendor = "Plastic Joe"
		# sp2.material = "PETG"
		#
		# allSpools = [sp1,sp2]

		tableQuery = flask.request.values

		allSpools = self._databaseManager.loadAllSpoolsByQuery(tableQuery)
		totalItemCount = self._databaseManager.countSpoolsByQuery()

		# allSpoolsAsDict = self._transformAllSpoolModelsToDict(allSpools)
		allSpoolsAsDict = Transformer.transformAllSpoolModelsToDict(allSpools)

		# load all catalogs: vendors, materials, labels, [colors]
		vendors = list(self._databaseManager.loadCatalogVendors(tableQuery))
		materials = list(self._databaseManager.loadCatalogMaterials(tableQuery))
		labels = list(self._databaseManager.loadCatalogLabels(tableQuery))
		colors = list(self._databaseManager.loadCatalogColors(tableQuery))

		materials = self._addAdditionalMaterials(materials)

		tempateSpoolAsDict = None
		allTemplateSpools = self._databaseManager.loadSpoolTemplate()
		if (allTemplateSpools != None):
			for spool in allTemplateSpools:
				tempateSpoolAsDict = Transformer.transformSpoolModelToDict(spool)
				break

		catalogs = {
			"vendors": vendors,
			"materials": materials,
			"colors": colors,
			"labels": labels
		}
		# catalogs = {
		# 	"materials": ["", "ABS", "PLA", "PETG"],
		# 	"colors": ["", "#123", "#456"],
		# 	"labels": ["", "good", "bad"]
		# }
		selectedSpoolsAsDicts = [
			(None if selectedSpool is None else Transformer.transformSpoolModelToDict(selectedSpool))
			for selectedSpool in self.loadSelectedSpools()
		]

		return flask.jsonify({
								# "databaseConnectionProblem": self._databaseManager.isConnected() == False,
								"templateSpool": tempateSpoolAsDict,
								"catalogs": catalogs,
								"totalItemCount": totalItemCount,
								"allSpools": allSpoolsAsDict,
								"selectedSpools": selectedSpoolsAsDicts
							})

	def _addAdditionalMaterials(self, databaseMaterials):

		allMeterials = [
			"PLA",
			"PLA_plus",
			"ABS",
			"PETG",
			"NYLON",
			"TPU",
			"PC",
			"Wood",
			"Carbon Fiber",
			"PC_ABS",
			"HIPS",
			"PVA",
			"ASA",
			"PP",
			"POM",
			"PMMA",
			"FPE"
		]
		for currentMaterial in allMeterials:
			if ( (currentMaterial.upper() in databaseMaterials) == False and (currentMaterial.lower() in databaseMaterials) == False):
				databaseMaterials.append(currentMaterial)
		return databaseMaterials


	#######################################################################################################   SAVE SPOOL
	@octoprint.plugin.BlueprintPlugin.route("/saveSpool", methods=["PUT"])
	def saveSpool(self):
		self._logger.info("API Save spool")
		jsonData = request.json

		databaseId = self._getValueFromJSONOrNone("databaseId", jsonData)
		self._databaseManager.connectoToDatabase()
		if (databaseId != None):
			self._logger.info("Update spool with database id '"+str(databaseId)+"'")
			spoolModel = self._databaseManager.loadSpool(databaseId, withReusedConnection=True)
			if (spoolModel == None):
				self._logger.warning("Save spool failed. Something is wrong")
			else:
				self._updateSpoolModelFromJSONData(spoolModel, jsonData)
		else:
			self._logger.info("Create new spool")
			spoolModel = SpoolModel()
			self._updateSpoolModelFromJSONData(spoolModel, jsonData)

		databaseId = self._databaseManager.saveSpool(spoolModel, withReusedConnection=True)
		self._databaseManager.closeDatabase()

		# data for the sidebar
		self.checkRemainingFilament()

		return flask.jsonify()


	#####################################################################################################   DELETE SPOOL
	@octoprint.plugin.BlueprintPlugin.route("/deleteSpool/<int:databaseId>", methods=["DELETE"])
	def deleteSpool(self, databaseId):
		self._logger.info("API Delete spool with database id '" + str(databaseId) + "'")
		printJob = self._databaseManager.deleteSpool(databaseId)
		# snapshotFilename = CameraManager.buildSnapshotFilename(printJob.printStartDateTime)
		# self._cameraManager.deleteSnapshot(snapshotFilename)
		# self._databaseManager.deletePrintJob(databaseId)
		return flask.jsonify()


