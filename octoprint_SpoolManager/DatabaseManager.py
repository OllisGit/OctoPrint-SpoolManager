# coding=utf-8
from __future__ import absolute_import

import json
import os
import logging

from octoprint_SpoolManager.WrappedLoggingHandler import WrappedLoggingHandler
from peewee import *

from octoprint_SpoolManager.models import SpoolModel
from octoprint_SpoolManager.models.BaseModel import BaseModel
from octoprint_SpoolManager.models.PluginMetaDataModel import PluginMetaDataModel
from octoprint_SpoolManager.models.SpoolModel import SpoolModel

FORCE_CREATE_TABLES = False

CURRENT_DATABASE_SCHEME_VERSION = 1

# List all Models
MODELS = [PluginMetaDataModel, SpoolModel]



class DatabaseManager(object):

	def __init__(self, parentLogger, sqlLoggingEnabled):
		self.sqlLoggingEnabled = sqlLoggingEnabled
		self._logger = logging.getLogger(parentLogger.name + "." + self.__class__.__name__)
		self._sqlLogger = logging.getLogger(parentLogger.name + "." + self.__class__.__name__ + ".SQL")

		self._database = None
		self._databaseFileLocation = None
		self._sendDataToClient = None

	################################################################################################## private functions

	def _createDatabase(self, forceCreateTables):
		self._database = SqliteDatabase(self._databaseFileLocation)
		DatabaseManager.db = self._database
		self._database.bind(MODELS)

		if forceCreateTables:
			self._logger.info("Creating new database-tables, because FORCE == TRUE!")
			self._createDatabaseTables()
		else:
			# check, if we need an scheme upgrade
			self._logger.info("Check if database-scheme upgrade needed.")
			self._createOrUpgradeSchemeIfNecessary()
		self._logger.info("Done DatabaseManager")


	def getDatabaseFileLocation(self):
		return self._databaseFileLocation

	def _createOrUpgradeSchemeIfNecessary(self):
		schemeVersionFromDatabaseModel = None
		try:
			schemeVersionFromDatabaseModel = PluginMetaDataModel.get(PluginMetaDataModel.key == PluginMetaDataModel.KEY_DATABASE_SCHEME_VERSION)
			pass
		except Exception as e:
			errorMessage = e.message
			if errorMessage.startswith("no such table"):
				self._createDatabaseTables()
			else:
				self._logger.error(str(e))

		if not schemeVersionFromDatabaseModel == None:
			currentDatabaseSchemeVersion = int(schemeVersionFromDatabaseModel.value)
			if (currentDatabaseSchemeVersion < CURRENT_DATABASE_SCHEME_VERSION):
				# evautate upgrade steps (from 1-2 , 1...6)
				print("We need to upgrade the database scheme from: '" + str(currentDatabaseSchemeVersion) + "' to: '" + str(CURRENT_DATABASE_SCHEME_VERSION) + "'")
				pass
		pass

		# databaseSchemeVersion = PluginMetaDataEntity.getDatabaseSchemeVersion(cursor)
		# if databaseSchemeVersion == None or FORCE_CREATE_TABLES == True:
		# 	self._createCurrentTables(cursor, FORCE_CREATE_TABLES)
		# else:
		# 	# check from which version we need to upgrade
		# 	#	sql
		# 	pass
	def _createDatabaseTables(self):
		self._logger.info("Creating new database tables for spoolmanager-plugin")
		self._database.connect(reuse_if_open=True)
		self._database.drop_tables(MODELS)
		self._database.create_tables(MODELS)

		PluginMetaDataModel.create(key=PluginMetaDataModel.KEY_DATABASE_SCHEME_VERSION, value=CURRENT_DATABASE_SCHEME_VERSION)
		self._database.close()

	################################################################################################### public functions
	# datapasePath '/Users/o0632/Library/Application Support/OctoPrint/data/PrintJobHistory'

	# def getDatabaseFileLocation(self):
	# 	return self._databaseFileLocation


	def initDatabase(self, databasePath, sendMessageToClient):
		self._logger.info("Init DatabaseManager")
		self.sendMessageToClient = sendMessageToClient
		self._databaseFileLocation = os.path.join(databasePath, "spoolmanager.db")

		self._logger.info("Creating database in: " + str(self._databaseFileLocation))

		import logging
		logger = logging.getLogger('peewee')
		# we need only the single logger without parent
		logger.parent = None
		# logger.addHandler(logging.StreamHandler())
		# activate SQL logging on PEEWEE side and on PLUGIN side
		# logger.setLevel(logging.DEBUG)
		# self._sqlLogger.setLevel(logging.DEBUG)
		self.showSQLLogging(self.sqlLoggingEnabled)

		wrappedHandler = WrappedLoggingHandler(self._sqlLogger)
		logger.addHandler(wrappedHandler)

		self._createDatabase(FORCE_CREATE_TABLES)

		pass

	def showSQLLogging(self, enabled):
		import logging
		logger = logging.getLogger('peewee')

		if (enabled):
			logger.setLevel(logging.DEBUG)
			self._sqlLogger.setLevel(logging.DEBUG)
		else:
			logger.setLevel(logging.ERROR)
			self._sqlLogger.setLevel(logging.ERROR)

	def loadSpool(self, databaseId):
		try:
			return SpoolModel.get_by_id(databaseId)
		except Exception as e:
			return None
		pass

	def loadSpoolTemplateSpool(self):
		return SpoolModel.select().where(SpoolModel.isTemplate == True)

	def saveModel(self, model):

		databaseId = None
		with self._database.atomic() as transaction:  # Opens new transaction.
			try:
				if (model.isTemplate == True):
					#  remove template flag from last templateSpool
					SpoolModel.update({SpoolModel.isTemplate: False}).where(SpoolModel.isTemplate == True).execute()

				model.save()
				databaseId = model.get_id()
				# do expicit commit
				transaction.commit()
			except Exception as e:
				# Because this block of code is wrapped with "atomic", a
				# new transaction will begin automatically after the call
				# to rollback().
				transaction.rollback()
				self._logger.exception("Could not insert printJob into database:" + str(e))

				self.sendErrorMessageToClient("error", "DatabaseManager", "Could not insert the printjob into the database. See OctoPrint.log for details!")
			pass

		return databaseId


	def loadAllSpoolsByQuery(self, tableQuery):
		if (tableQuery == None):
			return SpoolModel.select().order_by(SpoolModel.created.desc())

		offset = int(tableQuery["from"])
		limit = int(tableQuery["to"])
		sortColumn = tableQuery["sortColumn"]
		sortOrder = tableQuery["sortOrder"]
		# not needed at the moment filterName = tableQuery["filterName"]

		myQuery = SpoolModel.select().offset(offset).limit(limit)
		# if (filterName == "onlySuccess"):
		# 	myQuery = myQuery.where(PrintJobModel.printStatusResult == "success")
		# elif (filterName == "onlyFailed"):
		# 	myQuery = myQuery.where(PrintJobModel.printStatusResult != "success")

		if ("displayName" == sortColumn):
			if ("desc" == sortOrder):
				myQuery = myQuery.order_by(SpoolModel.displayName.desc())
			else:
				myQuery = myQuery.order_by(SpoolModel.displayName)
		if ("lastUse" == sortColumn):
			if ("desc" == sortOrder):
				myQuery = myQuery.order_by(SpoolModel.lastUse.desc())
			else:
				myQuery = myQuery.order_by(SpoolModel.lastUse)
		if ("firstUse" == sortColumn):
			if ("desc" == sortOrder):
				myQuery = myQuery.order_by(SpoolModel.firstUse.desc())
			else:
				myQuery = myQuery.order_by(SpoolModel.firstUse)
		return myQuery


	def countSpoolsByQuery(self, tableQuery):
		filterName = tableQuery["filterName"]

		myQuery = SpoolModel.select()
		# if (filterName == "onlySuccess"):
		# 	myQuery = myQuery.where(PrintJobModel.printStatusResult == "success")
		# elif (filterName == "onlyFailed"):
		# 	myQuery = myQuery.where(PrintJobModel.printStatusResult != "success")

		return myQuery.count()

	def loadCatalogVendors(self, tableQuery):
		result = set()
		result.add("")
		myQuery = SpoolModel.select(SpoolModel.vendor).distinct()
		for spool in myQuery:
			value = spool.vendor
			if (value != None):
				result.add(value)
		return result;

	def loadCatalogMaterials(self, tableQuery):
		result = set()
		result.add("")
		myQuery = SpoolModel.select(SpoolModel.material).distinct()
		for spool in myQuery:
			value = spool.material
			if (value != None):
				result.add(value)
		return result;

	def loadCatalogLabels(self, tableQuery):
		result = set()
		result.add("")
		myQuery = SpoolModel.select(SpoolModel.labels).distinct()
		for spool in myQuery:
			value = spool.labels
			if (value != None):
				spoolLabels = json.loads(value)
				for singleLabel in spoolLabels:
					result.add(singleLabel)
		return result;

	def deleteSpool(self, databaseId):
		with self._database.atomic() as transaction:  # Opens new transaction.
			try:
				# first delete relations
				# n = FilamentModel.delete().where(FilamentModel.printJob == databaseId).execute()
				# n = TemperatureModel.delete().where(TemperatureModel.printJob == databaseId).execute()

				SpoolModel.delete_by_id(databaseId)
			except Exception as e:
				# Because this block of code is wrapped with "atomic", a
				# new transaction will begin automatically after the call
				# to rollback().
				transaction.rollback()
				self._logger.exception("Could not delete spool from database:" + str(e))

				self.sendErrorMessageToClient("Spool-DatabaseManager", "Could not delete the spool ('"+ str(databaseId) +"') from the database. See OctoPrint.log for details!")
			pass
