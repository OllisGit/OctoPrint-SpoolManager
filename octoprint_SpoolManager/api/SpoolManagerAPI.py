# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import datetime
import flask
from flask import jsonify, request, make_response, Response, send_file
import json

from octoprint_SpoolManager.models.SpoolModel import SpoolModel
from octoprint_SpoolManager.common import StringUtils
from octoprint_SpoolManager.api import Transformer
from octoprint_SpoolManager.common.SettingsKeys import SettingsKeys

class SpoolManagerAPI(octoprint.plugin.BlueprintPlugin):

	def _updateSpoolModelFromJSONData(self, spoolModel, jsonData):

		spoolModel.databaseId = self._getValueFromJSONOrNone("databaseId", jsonData)
		spoolModel.isTemplate = self._getValueFromJSONOrNone("isTemplate", jsonData)
		spoolModel.displayName = self._getValueFromJSONOrNone("displayName", jsonData)
		spoolModel.vendor = self._getValueFromJSONOrNone("vendor", jsonData)
		spoolModel.material = self._getValueFromJSONOrNone("material", jsonData)
		spoolModel.density = self._getValueFromJSONOrNone("density", jsonData)
		spoolModel.diameter = self._getValueFromJSONOrNone("diameter", jsonData)
		spoolModel.color = self._getValueFromJSONOrNone("color", jsonData)
		spoolModel.temperature = self._getValueFromJSONOrNone("temperature", jsonData)
		spoolModel.totalWeight = self._getValueFromJSONOrNone("totalWeight", jsonData)
		spoolModel.remainingWeight = self._getValueFromJSONOrNone("remainingWeight", jsonData)
		spoolModel.usedLength = self._getValueFromJSONOrNone("usedLength", jsonData)
		spoolModel.usedWeight = self._getValueFromJSONOrNone("usedWeight", jsonData)
		spoolModel.code = self._getValueFromJSONOrNone("code", jsonData)

		spoolModel.firstUse = StringUtils.transformToDateTimeOrNone(self._getValueFromJSONOrNone("firstUse", jsonData))
		spoolModel.lastUse = StringUtils.transformToDateTimeOrNone(self._getValueFromJSONOrNone("lastUse", jsonData))
		spoolModel.purchasedOn = StringUtils.transformToDateTimeOrNone(self._getValueFromJSONOrNone("purchasedOn", jsonData))

		spoolModel.purchasedFrom = self._getValueFromJSONOrNone("purchasedFrom", jsonData)
		spoolModel.cost = self._getValueFromJSONOrNone("cost", jsonData)
		spoolModel.costUnit = self._getValueFromJSONOrNone("costUnit", jsonData)

		spoolModel.labels = json.dumps(self._getValueFromJSONOrNone("labels", jsonData))

		spoolModel.noteText = self._getValueFromJSONOrNone("noteText", jsonData)
		spoolModel.noteDeltaFormat = json.dumps(self._getValueFromJSONOrNone("noteDeltaFormat", jsonData))
		spoolModel.noteHtml = self._getValueFromJSONOrNone("noteHtml", jsonData)
		pass

	# def _transformSpoolModelToDict(self, spoolModel):
	# 	spoolAsDict = spoolModel.__data__
	#
	# 	spoolAsDict["firstUse"] = StringUtils.formatDateTime(spoolModel.firstUse)
	# 	spoolAsDict["lastUse"] = StringUtils.formatDateTime(spoolModel.lastUse)
	# 	spoolAsDict["purchasedOn"] = StringUtils.formatDateTime(spoolModel.purchasedOn)
	#
	#
	#
	# 	# Decimal and date time needs to be converted
	#
	# 	# spoolAsDict["temperature"] = StringUtils.formatSave("{:.02f}", spoolAsDict["temperature"], "")
	# 	# spoolAsDict["weight"] = StringUtils.formatSave("{:.02f}", spoolAsDict["weight"], "")
	# 	# spoolAsDict["remainingWeight"] = StringUtils.formatSave("{:.02f}", spoolAsDict["remainingWeight"], "")
	# 	# spoolAsDict["usedLength"] = StringUtils.formatSave("{:.02f}", spoolAsDict["usedLength"], "")
	# 	# spoolAsDict["usedLength"] = StringUtils.formatSave("{:.02f}", spoolAsDict["usedLength"], "")
	#
	# 	# spoolAsDict["firstUse"] = spoolModel.firstUse.strftime('%d.%m.%Y %H:%M')
	# 	# spoolAsDict["lastUse"] = spoolModel.lastUse.strftime('%d.%m.%Y %H:%M')
	#
	# 	# spoolAsDict["firstUse"] = self._formatDateOrNone( spoolModel.firstUse )
	# 	# spoolAsDict["lastUse"] = self._formatDateOrNone( spoolModel.lastUse )
	#
	#
	# 	return spoolAsDict
	#
	# def _transformAllSpoolModelsToDict(self, allSpoolModels):
	# 	result = []
	# 	for job in allSpoolModels:
	# 		spoolAsDict = self._transformSpoolModelToDict(job)
	# 		result.append(spoolAsDict)
	# 	return result

	def _getValueFromJSONOrNone(self, key, json):
		if key in json:
			return json[key]
		return None

	# def _formatDateOrNone(self, dateValue):
	# 	if dateValue != None:
	# 		return dateValue.strftime('%d.%m.%Y %H:%M')
	# 	return None
	# def _formatDateOrNone(self, dateValue):
	# 	if dateValue != None:
	# 		return datetime.strptime(str(dateValue), '%d.%m.%Y %H:%M')
	# 	return None

	def loadSelectedSpool(self):
		spoolModel = None

		databaseId = self._settings.get_int([SettingsKeys.SETTINGS_KEY_SELECTED_SPOOL_DATABASE_ID])
		if (databaseId != None):
			spoolModel = self._databaseManager.loadSpool(databaseId)

		return spoolModel

	################################################### APIs

	##############################################################################################   ALLOWED TO PRINT
	@octoprint.plugin.BlueprintPlugin.route("/allowedToPrint", methods=["GET"])
	def allowed_to_print(self):

		checkForSelectedSpool = self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_WARN_IF_SPOOL_NOT_SELECTED])
		checkForFilamentLength = self._settings.get_boolean([SettingsKeys.SETTINGS_KEY_WARN_IF_FILAMENT_NOT_ENOUGH])

		if (checkForFilamentLength == False and checkForSelectedSpool == False):
			return flask.jsonify({
				"result": "startPrint"
			})

		spoolModel = self.loadSelectedSpool()

		if (checkForSelectedSpool == True and spoolModel == None):
			return flask.jsonify({
				"result": "noSpoolSelected",
			})

		if (checkForFilamentLength == True):
			# check if loaded
			if (spoolModel == None):
				return flask.jsonify({
					"result": "noSpoolForUsageCheck",
				})
			else:
				result = self.checkRemainingFilament();
				if (result == False):
					return flask.jsonify({
						"result": "filamentNotEnough",
					})

		return flask.jsonify({
			"result": "startPrint"
		})

	#####################################################################################################   SELECT SPOOL
	@octoprint.plugin.BlueprintPlugin.route("/selectSpool", methods=["PUT"])
	def select_spool(self):
		jsonData = request.json

		databaseId = self._getValueFromJSONOrNone("databaseId", jsonData)
		if (databaseId != None):
			spoolModel = self._databaseManager.loadSpool(databaseId)
			# check if loaded
			if (spoolModel != None):
				# - store spool in Settings
				self._settings.set_int([SettingsKeys.SETTINGS_KEY_SELECTED_SPOOL_DATABASE_ID], databaseId)
				self._settings.save()

				self.checkRemainingFilament()
		else:
			# No selection
			self._settings.set_int([SettingsKeys.SETTINGS_KEY_SELECTED_SPOOL_DATABASE_ID], None)
			self._settings.save()
			pass

		# databaseId = self._databaseManager.saveModel(spoolModel)

		return flask.jsonify()


	##################################################################################################   LOAD ALL SPOOLS
	@octoprint.plugin.BlueprintPlugin.route("/loadSpoolsByQuery", methods=["GET"])
	def load_allSpools(self):

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
		totalItemCount = self._databaseManager.countSpoolsByQuery(tableQuery)

		# allSpoolsAsDict = self._transformAllSpoolModelsToDict(allSpools)
		allSpoolsAsDict = Transformer.transformAllSpoolModelsToDict(allSpools)

		# load all catalogs: vendors, materials, labels, [colors]
		vendors = list(self._databaseManager.loadCatalogVendors(tableQuery))
		materials = list(self._databaseManager.loadCatalogMaterials(tableQuery))
		labels = list(self._databaseManager.loadCatalogLabels(tableQuery))

		tempateSpoolAsDict = None
		allTemplateSpools = self._databaseManager.loadSpoolTemplateSpool()
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

		return flask.jsonify({
								"templateSpool": tempateSpoolAsDict,
								"catalogs": catalogs,
								"totalItemCount": totalItemCount,
								"allSpools": allSpoolsAsDict
							})


	#######################################################################################################   SAVE SPOOL
	@octoprint.plugin.BlueprintPlugin.route("/saveSpool", methods=["PUT"])
	def save_spool(self):
		jsonData = request.json

		databaseId = self._getValueFromJSONOrNone("databaseId", jsonData)
		if (databaseId != None):
			spoolModel = self._databaseManager.loadSpool(databaseId)
			self._updateSpoolModelFromJSONData(spoolModel, jsonData)
		else:
			spoolModel = SpoolModel()
			self._updateSpoolModelFromJSONData(spoolModel, jsonData)

		databaseId = self._databaseManager.saveModel(spoolModel)

		return flask.jsonify()


	#####################################################################################################   DELETE SPOOL
	@octoprint.plugin.BlueprintPlugin.route("/deleteSpool/<int:databaseId>", methods=["DELETE"])
	def delete_printjob(self, databaseId):
		printJob = self._databaseManager.deleteSpool(databaseId)
		# snapshotFilename = CameraManager.buildSnapshotFilename(printJob.printStartDateTime)
		# self._cameraManager.deleteSnapshot(snapshotFilename)
		# self._databaseManager.deletePrintJob(databaseId)
		return flask.jsonify()
