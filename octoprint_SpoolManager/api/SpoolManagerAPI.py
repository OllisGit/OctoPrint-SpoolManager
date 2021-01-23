# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import datetime
import flask
from flask import jsonify, request, make_response, Response, send_file
import json
import shutil
import tempfile
import threading
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
		spoolModel.encloserTemperature = self._toIntFromJSONOrNone("encloserTemperature", jsonData)
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

	def loadSelectedSpool(self, ):
		spoolModel = None
		databaseId = self._settings.get_int([SettingsKeys.SETTINGS_KEY_SELECTED_SPOOL_DATABASE_ID])

		if (databaseId != None):
			self._databaseManager.connectoToDatabase()
			spoolModel = self._databaseManager.loadSpool(databaseId)
			self._databaseManager.closeConnection()
			if (spoolModel == None):
				self._logger.warning(
					"Last selected Spool from plugin-settings not found in database. Maybe deleted in the meantime.")

		return spoolModel


	def _createSampleSpoolModel(self):
		#DisplayName, Vendor, Material, Color[# code], Diameter [mm], Density [g/cm³], Temperature [°C], TotalWeight [g], UsedWeight [g], UsedLength [mm], FirstUse [dd.mm.yyyy hh:mm], LastUse [dd.mm.yyyy hh:mm], PurchasedFrom, PurchasedOn [dd.mm.yyyy hh:mm], Cost, CostUnit, Labels, NoteText

		s1 = SpoolModel()
		s1.displayName = "Number #1"
		s1.colorName = "raw-red"
		s1.color = "#FF0000"
		s1.vendor = "The Spool Company"
		s1.material = "PETG"
		s1.diameter = 1.75
		s1.diameterTolerance = 0.2
		s1.density = 1.27
		s1.flowRateCompensation = 110
		s1.temperature = 182
		s1.bedtemperature = 52
		s1.encloserTemperature = 23
		s1.totalWeight = 1000.0
		s1.spoolWeight = 12.3
		s1.usedWeight = 123.4
		s1.totalLength = 1321
		s1.usedLength = 234
		s1.lastUse = datetime.datetime.now()

		s1.firstUse = datetime.datetime.strptime("2020-03-02 10:33", '%Y-%m-%d %H:%M')
		s1.purchasedOn = datetime.datetime.strptime("2020-02-01", '%Y-%m-%d')
		s1.purchasedFrom = "Unknown Seller"
		s1.cost = "12.30"
		s1.costUnit = "€"
		s1.noteText = "Very cheap spool!"
		return s1



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


	def _selectSpool(self, databaseId):
		spoolModel = None
		if (databaseId != None):
			spoolModel = self._databaseManager.loadSpool(databaseId)
			# check if loaded
			if (spoolModel != None):
				self._logger.info("Store selected spool '"+spoolModel.displayName+"' in settings.")

				# - store spool in Settings
				self._settings.set_int([SettingsKeys.SETTINGS_KEY_SELECTED_SPOOL_DATABASE_ID], databaseId)
				self._settings.save()

				self.checkRemainingFilament()
			else:
				self._logger.warning("Selected Spool with id '"+str(databaseId)+"' not in database anymore. Maybe deleted in the meantime.")

		if spoolModel == None:
			# No selection
			self._logger.info("Clear stored selected spool in settings.")
			self._settings.set_int([SettingsKeys.SETTINGS_KEY_SELECTED_SPOOL_DATABASE_ID], None)
			self._settings.save()
			pass

		return spoolModel


	################################################### APIs

	@octoprint.plugin.BlueprintPlugin.route("/sampleCSV", methods=["GET"])
	def get_sampleCSV(self):

		allSpoolModels = list()

		spoolModel = self._createSampleSpoolModel()
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

		if (checkForFilamentLength == False and checkForSelectedSpool == False):
			return flask.jsonify({
				"result": "startPrint"
			})

		spoolModel = self.loadSelectedSpool()

		if (checkForSelectedSpool == True and spoolModel == None):
			return flask.jsonify({
				"result": "noSpoolSelected",
			})

		if (checkForFilamentLength == True and spoolModel != None):
			# # check if loaded
			# if (spoolModel == None):
			# 	return flask.jsonify({
			# 		"result": "noSpoolForUsageCheck",
			# 	})
			# else:
			result = self.checkRemainingFilament()
			if (result == False):
				return flask.jsonify({
					"result": "filamentNotEnough",
				})

		if (reminderSelectingSpool == True and spoolModel != None):
			return flask.jsonify({
				"result": "reminderSpoolSelection",
				"spoolName": spoolModel.displayName
			})

		return flask.jsonify({
			"result": "startPrint"
		})

	#####################################################################################################   SELECT SPOOL
	@octoprint.plugin.BlueprintPlugin.route("/selectSpool", methods=["PUT"])
	def select_spool(self):
		self._logger.info("API Store selected spool")
		jsonData = request.json

		databaseId = self._getValueFromJSONOrNone("databaseId", jsonData)

		spoolModel = self._selectSpool(databaseId)

		spoolModelAsDict = None
		if (spoolModel != None):
			spoolModelAsDict = Transformer.transformSpoolModelToDict(spoolModel)

		return flask.jsonify({
								"selectedSpool": spoolModelAsDict
							})

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
				self._selectSpool(None)

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
	def download_database(self):
		return send_file(self._databaseManager.getDatabaseFileLocation(),
						 mimetype='application/octet-stream',
						 attachment_filename='spoolmanager.db',
						 as_attachment=True)


	#######################################################################################   DELETE DATABASE
	@octoprint.plugin.BlueprintPlugin.route("/deleteDatabase/<string:databaseType>", methods=["POST"])
	def delete_database(self, databaseType):

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
	def load_allSpools(self):

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
			"labels": labels
		}
		# catalogs = {
		# 	"materials": ["", "ABS", "PLA", "PETG"],
		# 	"colors": ["", "#123", "#456"],
		# 	"labels": ["", "good", "bad"]
		# }
		selectedSpoolAsDict = None
		selectedSpool = self.loadSelectedSpool()
		if (selectedSpool):
			selectedSpoolAsDict = Transformer.transformSpoolModelToDict(selectedSpool)
		else:
			# spool not found
			pass

		return flask.jsonify({
								"databaseConnectionProblem": self._databaseManager.isConnected() == False,
								"templateSpool": tempateSpoolAsDict,
								"catalogs": catalogs,
								"totalItemCount": totalItemCount,
								"allSpools": allSpoolsAsDict,
								"selectedSpool": selectedSpoolAsDict
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
	def save_spool(self):
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

		return flask.jsonify()


	#####################################################################################################   DELETE SPOOL
	@octoprint.plugin.BlueprintPlugin.route("/deleteSpool/<int:databaseId>", methods=["DELETE"])
	def delete_spool(self, databaseId):
		self._logger.info("API Delete spool with database id '" + str(databaseId) + "'")
		printJob = self._databaseManager.deleteSpool(databaseId)
		# snapshotFilename = CameraManager.buildSnapshotFilename(printJob.printStartDateTime)
		# self._cameraManager.deleteSnapshot(snapshotFilename)
		# self._databaseManager.deletePrintJob(databaseId)
		return flask.jsonify()


