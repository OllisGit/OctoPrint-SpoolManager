# coding=utf-8
from __future__ import absolute_import

import datetime
import json
import os
import logging
import shutil
import sqlite3

from octoprint_SpoolManager.WrappedLoggingHandler import WrappedLoggingHandler
from peewee import *

from octoprint_SpoolManager.api import Transformer
from octoprint_SpoolManager.models import SpoolModel
from octoprint_SpoolManager.models.BaseModel import BaseModel
from octoprint_SpoolManager.models.PluginMetaDataModel import PluginMetaDataModel
from octoprint_SpoolManager.models.SpoolModel import SpoolModel

FORCE_CREATE_TABLES = False

CURRENT_DATABASE_SCHEME_VERSION = 3

# List all Models
MODELS = [PluginMetaDataModel, SpoolModel]



class DatabaseManager(object):

	class DatabaseSettings:
		useExternal = False
		# Internal stuff
		baseFolder = ""
		fileLocation = ""
		# External stuff
		type = "postgresql" # sqlite, mysql, postgresql
		name = ""
		host = ""
		port = 0
		user = ""
		password = ""

		def __str__(self):
			return str(self.__dict__)

	def __init__(self, parentLogger, sqlLoggingEnabled):
		self.sqlLoggingEnabled = sqlLoggingEnabled
		self._logger = logging.getLogger(parentLogger.name + "." + self.__class__.__name__)
		self._sqlLogger = logging.getLogger(parentLogger.name + "." + self.__class__.__name__ + ".SQL")

		self._database = None
		self._databseSettings = None
		self._sendDataToClient = None
		self._isConnected = False
		self._currentErrorMessageDict = None

	################################################################################################## private functions
	# "databaseSettings"] = {
	# "useExternal": "true",
	# "type": "postgres",
	# "host": "localhost",
	# "port": 5432,
	# "databaseName": "SpoolManagerDatabase",
	# "user": "Olli",
	# "password": "illO"

	def _buildDatabaseConnection(self, databaseSettings):
		database = None
		if (databaseSettings.useExternal == False):
			# local database
			database = SqliteDatabase(databaseSettings.fileLocation)
		else:
			databaseType = databaseSettings.type
			databaseName = databaseSettings.name
			host = databaseSettings.host
			port = databaseSettings.port
			user = databaseSettings.user
			password = databaseSettings.password
			if ("postgres" == databaseType):
				# Connect to a Postgres database.
				database = PostgresqlDatabase(databaseName,
												   	user=user,
												   	password=password,
										   		   	host=host,
												   	port=port)
			else:
				# Connect to a MySQL database on network.
				database = MySQLDatabase(databaseName,
											   user=user,
											   password=password,
											   host=host,
											   port=port)

		return database

	def _createDatabase(self, forceCreateTables, databaseSettings=None):
		# self._database = SqliteDatabase(self._databaseFileLocation)
		# DatabaseManager.db = self._database
		# self._database.bind(MODELS)

		if (databaseSettings != None):
			currentDatabaseSettings = self._databaseSettings
			self.connectoToDatabase(databaseSettings)

		if forceCreateTables:
			self._logger.info("Creating new database-tables, because FORCE == TRUE!")
			self._createDatabaseTables()
		else:
			# check, if we need an scheme upgrade
			self._createOrUpgradeSchemeIfNecessary()

		if (databaseSettings != None):
			self.closeDatabase();
			self._databaseSettings = currentDatabaseSettings
			# self.connectoToDatabase(self._databaseSettings)

		self._logger.info("Done DatabaseManager")

	def _createOrUpgradeSchemeIfNecessary(self):

		self._logger.info("Check if database-scheme upgrade needed...")
		schemeVersionFromDatabaseModel = None
		try:
			schemeVersionFromDatabaseModel = PluginMetaDataModel.get(PluginMetaDataModel.key == PluginMetaDataModel.KEY_DATABASE_SCHEME_VERSION)
			pass
		except Exception as e:
			self.closeDatabase()
			errorMessage = str(e)
			if (
				# - SQLLite
				errorMessage.startswith("no such table") or
				# - Postgres
				"does not exist" in errorMessage
			):
				self._createDatabaseTables()
			else:
				self._logger.error(str(e))

		if not schemeVersionFromDatabaseModel == None:
			currentDatabaseSchemeVersion = int(schemeVersionFromDatabaseModel.value)
			if (currentDatabaseSchemeVersion < CURRENT_DATABASE_SCHEME_VERSION):
				# auto upgrade done only for local database
				if (self._databaseSettings.useExternal == True):
					self._logger.info("Scheme upgrade is only done for local database")
					return

				# evautate upgrade steps (from 1-2 , 1...6)
				self._logger.info("We need to upgrade the database scheme from: '" + str(currentDatabaseSchemeVersion) + "' to: '" + str(CURRENT_DATABASE_SCHEME_VERSION) + "'")

				try:
					self.backupDatabaseFile()
					self._upgradeDatabase(currentDatabaseSchemeVersion, CURRENT_DATABASE_SCHEME_VERSION)
				except Exception as e:
					self._logger.error("Error during database upgrade!!!!")
					self._logger.exception(e)
					return
				self._logger.info("...Database-scheme successfully upgraded.")
		else:
			self._logger.info("...Database-scheme upgraded not needed.")
		pass


	def _upgradeDatabase(self,currentDatabaseSchemeVersion, targetDatabaseSchemeVersion):

		migrationFunctions = [self._upgradeFrom1To2, self._upgradeFrom2To3, self._upgradeFrom3To4, self._upgradeFrom4To5]

		for migrationMethodIndex in range(currentDatabaseSchemeVersion -1, targetDatabaseSchemeVersion -1):
			self._logger.info("Database migration from '" + str(migrationMethodIndex + 1) + "' to '" + str(migrationMethodIndex + 2) + "'")
			migrationFunctions[migrationMethodIndex]()
			pass
		pass


	def _upgradeFrom4To5(self):
		self._logger.info(" Starting 4 -> 5")


	def _upgradeFrom3To4(self):
		self._logger.info(" Starting 3 -> 4")


	def _upgradeFrom2To3(self):
		self._logger.info(" Starting 2 -> 3")
		# What is changed:
		# - version = IntegerField(null=True)  # since V3
		# - diameterTolerance = FloatField(null=True)  # since V3
		# - flowRateCompensation = IntegerField(null=True)  # since V3
		# - bedTemperature = IntegerField(null=True)  # since V3
		# - encloserTemperature = IntegerField(null=True)  # since V3

		connection = sqlite3.connect(self._databaseFileLocation)
		cursor = connection.cursor()

		sql = """
		PRAGMA foreign_keys=off;
		BEGIN TRANSACTION;

			ALTER TABLE 'spo_spoolmodel' ADD 'version' INTEGER;
			ALTER TABLE 'spo_spoolmodel' ADD 'diameterTolerance' REAL;
			ALTER TABLE 'spo_spoolmodel' ADD 'spoolWeight' REAL;
			ALTER TABLE 'spo_spoolmodel' ADD 'flowRateCompensation' INTEGER;
			ALTER TABLE 'spo_spoolmodel' ADD 'bedTemperature' INTEGER;
			ALTER TABLE 'spo_spoolmodel' ADD 'encloserTemperature' INTEGER;
			ALTER TABLE 'spo_spoolmodel' ADD 'totalLength' INTEGER;

			UPDATE 'spo_spoolmodel' SET version=1;

			UPDATE 'spo_pluginmetadatamodel' SET value=3 WHERE key='databaseSchemeVersion';
		COMMIT;
		PRAGMA foreign_keys=on;
		"""
		cursor.executescript(sql)

		connection.close()

		self._logger.info(" Successfully 2 -> 3")
		pass

	def _upgradeFrom1To2(self):
		self._logger.info(" Starting 1 -> 2")
		# What is changed:
		# - SpoolModel: Add Column colorName
		# - SpoolModel: Add Column remainingWeight (needed fro filtering, sorting)
		connection = sqlite3.connect(self._databaseFileLocation)
		cursor = connection.cursor()

		sql = """
		PRAGMA foreign_keys=off;
		BEGIN TRANSACTION;

			ALTER TABLE 'spo_spoolmodel' ADD 'colorName' VARCHAR(255);
			ALTER TABLE 'spo_spoolmodel' ADD 'remainingWeight' REAL;

			UPDATE 'spo_pluginmetadatamodel' SET value=2 WHERE key='databaseSchemeVersion';
		COMMIT;
		PRAGMA foreign_keys=on;
		"""
		cursor.executescript(sql)

		connection.close()
		self._logger.info("Database 'altered' successfully. Try to calculate remaining weight.")
		#  Calculate the remaining weight for all current spools
		with self._database.atomic() as transaction:  # Opens new transaction.
			try:

				allSpoolModels = self.loadAllSpoolsByQuery(None)
				if (allSpoolModels != None):
					for spoolModel in allSpoolModels:
						totalWeight = spoolModel.totalWeight
						usedWeight = spoolModel.usedWeight
						remainingWeight = Transformer.calculateRemainingWeight(usedWeight, totalWeight)
						if (remainingWeight != None):
							spoolModel.remainingWeight = remainingWeight
							spoolModel.save()

				# do expicit commit
				transaction.commit()
			except Exception as e:
				# Because this block of code is wrapped with "atomic", a
				# new transaction will begin automatically after the call
				# to rollback().
				transaction.rollback()
				self._logger.exception("Could not upgrade database scheme from 1 To 2:" + str(e))

				self._passMessageToClient("error", "DatabaseManager", "Could not upgrade database scheme V1 to V2. See OctoPrint.log for details!")
			pass

		self._logger.info(" Successfully 1 -> 2")
		pass


	def _createDatabaseTables(self):
		self._logger.info("Creating new database tables for spoolmanager-plugin")
		self._database.connect(reuse_if_open=True)
		self._database.drop_tables(MODELS)
		self._database.create_tables(MODELS)

		PluginMetaDataModel.create(key=PluginMetaDataModel.KEY_DATABASE_SCHEME_VERSION, value=CURRENT_DATABASE_SCHEME_VERSION)
		self.closeDatabase()

	def _storeErrorMessage(self, type, title, message, sendErrorPopUp):
		# store current error message
		self._currentErrorMessageDict = {
			"type":type,
			"title":title,
			"message":message
		}
		# send to client, if needed
		if (sendErrorPopUp == True):
			self._passMessageToClient(type, title, message)

	################################################################################################### public functions
	@staticmethod
	def getDatabaseFileLocation(pluginDataBaseFolder):
		databaseFileLocation = os.path.join(pluginDataBaseFolder, "spoolmanager.db")
		return databaseFileLocation


	def initDatabase(self, databaseSettings, sendMessageToClient):

		self._logger.info("Init DatabaseManager")
		self._currentErrorMessageDict = None
		self._passMessageToClient = sendMessageToClient
		self._databaseSettings = databaseSettings

		databaseFileLocation = DatabaseManager.getDatabaseFileLocation(databaseSettings.baseFolder)
		self._databaseSettings.fileLocation = databaseFileLocation

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

		self.connectoToDatabase(self._databaseSettings, sendErrorPopUp=False)
		if (self._isConnected == True):
			self._createDatabase(FORCE_CREATE_TABLES)

		return self._currentErrorMessageDict

	def getCurrentErrorMessageDict(self):
		return self._currentErrorMessageDict

	#
	def reConnectToDatabase(self):
		return self.connectoToDatabase(self._databaseSettings, sendErrorPopUp=False)

	#
	def connectoToDatabase(self, databaseSettings, sendErrorPopUp=True) :
		# reset current errorDict
		self._currentErrorMessageDict = None
		self._isConnected = False

		# build connection
		self._databaseSettings = databaseSettings
		self._logger.info("Databaseconnection with...")
		self._logger.info(databaseSettings)
		self._database = self._buildDatabaseConnection(databaseSettings)

		# connect to Database
		DatabaseManager.db = self._database
		self._database.bind(MODELS)

		try:
			self._database.connect()
			self._logger.info("Database connection succesful. Checking Scheme versions")
			schemeVersionFromPlugin = str(CURRENT_DATABASE_SCHEME_VERSION)
			schemeVersionFromDatabaseModel = str(PluginMetaDataModel.get(PluginMetaDataModel.key == PluginMetaDataModel.KEY_DATABASE_SCHEME_VERSION).value)
			if (schemeVersionFromPlugin != schemeVersionFromDatabaseModel):
				errorMessage = "Plugin needs database scheme version: "+str(schemeVersionFromPlugin)+", but database has version: "+str(schemeVersionFromDatabaseModel);
				self._storeErrorMessage("error", "database scheme version", errorMessage , False)
				self._logger.error(errorMessage)
				self._isConnected = False
			else:
				self._logger.info("...succesfull connected")
				self._isConnected = True
		except Exception as e:
			errorMessage = str(e)
			self._logger.error(errorMessage)
			self.closeDatabase()
			# type, title, message
			self._storeErrorMessage("error", "connection problem", errorMessage, sendErrorPopUp)
			return False
		return self._isConnected

	def closeDatabase(self, ) :
		self._currentErrorMessageDict = None
		try:
			self._database.close()
			pass
		except Exception as e:
			pass ## ignore close exception
		self._isConnected = False

	def isConnected(self):
		return self._isConnected

	def showSQLLogging(self, enabled):
		import logging
		logger = logging.getLogger('peewee')

		if (enabled):
			logger.setLevel(logging.DEBUG)
			self._sqlLogger.setLevel(logging.DEBUG)
		else:
			logger.setLevel(logging.ERROR)
			self._sqlLogger.setLevel(logging.ERROR)


	def backupDatabaseFile(self):
		now = datetime.datetime.now()
		currentDate = now.strftime("%Y%m%d-%H%M")
		backupDatabaseFilePath = self._databaseFileLocation[0:-3] + "-backup-"+currentDate+".db"
		# backupDatabaseFileName = "spoolmanager-backup-"+currentDate+".db"
		# backupDatabaseFilePath = os.path.join(backupFolder, backupDatabaseFileName)
		if not os.path.exists(backupDatabaseFilePath):
			shutil.copy(self._databaseFileLocation, backupDatabaseFilePath)
			self._logger.info("Backup of spoolmanager database created '"+backupDatabaseFilePath+"'")
		else:
			self._logger.warn("Backup of spoolmanager database ('" + backupDatabaseFilePath + "') is already present. No backup created.")
		return backupDatabaseFilePath

	def reCreateDatabase(self, databaseSettings):
		self._currentErrorMessageDict = None
		self._logger.info("ReCreating Database")
		self._createDatabase(True, databaseSettings)

	################################################################################################ DATABASE OPERATIONS
	def loadDatabaseMetaInformations(self, databaseSettings):
		if (databaseSettings == None):
			# use current Settings
			databaseSettings = self._databaseSettings
		else:
			# add localFilepath
			databaseSettings.baseFolder = self._databaseSettings.baseFolder
			databaseSettings.fileLocation = self._databaseSettings.fileLocation
		# filelocation
		# backupname
		# scheme version
		# spoolitem count
		schemeVersionFromPlugin = CURRENT_DATABASE_SCHEME_VERSION
		localSchemeVersionFromDatabaseModel = "-"
		localSpoolItemCount = "-"
		externalSchemeVersionFromDatabaseModel = "-"
		externalSpoolItemCount = "-"
		errorMessage = ""

		# - save current DatbaseSettings
		currentDatabaseSettings = self._databaseSettings
		currentDatabase = self._database
		externalConnected = False
		# always read local meta data
		try:
			# TODO filelocation and maybe backupfilename
			shouldUseExternal = databaseSettings.useExternal
			databaseSettings.useExternal= False
			self.connectoToDatabase(databaseSettings, sendErrorPopUp=False)
			localSchemeVersionFromDatabaseModel = PluginMetaDataModel.get(PluginMetaDataModel.key == PluginMetaDataModel.KEY_DATABASE_SCHEME_VERSION).value
			localSpoolItemCount = self.countSpoolsByQuery()
			self.closeDatabase()

			databaseSettings.useExternal = shouldUseExternal

			if (shouldUseExternal == True):
				# External DB
				externalConnected = self.connectoToDatabase(databaseSettings, sendErrorPopUp=False)
				externalSchemeVersionFromDatabaseModel = PluginMetaDataModel.get(PluginMetaDataModel.key == PluginMetaDataModel.KEY_DATABASE_SCHEME_VERSION).value
				externalSpoolItemCount = self.countSpoolsByQuery()
				self.closeDatabase()
		except Exception as e:
			errorMessage = str(e)
			self._logger.exception(e)
			try:
				self.closeDatabase()
			except Exception:
				pass #ignore close exception

		# - restore/reconnect current DatabaseSettings
		self._databaseSettings = currentDatabaseSettings
		self._database = currentDatabase
		self.connectoToDatabase(self._databaseSettings, sendErrorPopUp=False)

		return {
			"success": externalConnected,
			"errorMessage": errorMessage,
			"schemeVersionFromPlugin": schemeVersionFromPlugin,
			"localSchemeVersionFromDatabaseModel": localSchemeVersionFromDatabaseModel,
			"localSpoolItemCount": localSpoolItemCount,
			"externalSchemeVersionFromDatabaseModel": externalSchemeVersionFromDatabaseModel,
			"externalSpoolItemCount": externalSpoolItemCount
		}


	def loadSpool(self, databaseId):
		if (self._isConnected == False):
			self._logger.error("Database not connected. Check database-settings!")
			return

		try:
			return SpoolModel.get_by_id(databaseId)
		except Exception as e:
			return None
		pass


	def loadSpoolTemplateSpool(self):
		if (self._isConnected == False):
			self._logger.error("Database not connected. Check database-settings!")
			return

		return SpoolModel.select().where(SpoolModel.isTemplate == True)


	def saveModel(self, model):
		if (self._isConnected == False):
			self._logger.error("Database not connected. Check database-settings!")
			return

		# databaseId = model.get_id()
		# if (databaseId != None):
		# 	# we need to update and we need to make
		# 	spoolModel = self.loadSpool(databaseId)
		# 	if (spoolModel == None):
		# 		self._passMessageToClient("error", "DatabaseManager",
		# 								  "Could not update the Spool, because it is already deleted!")
		# 		return
		# 	else:
		# 		versionFromUI = model.version if model.version != None else 1
		# 		versionFromDatabase = spoolModel.version if spoolModel.version != None else 1
		# 		if (versionFromUI != versionFromDatabase):
		# 			self._passMessageToClient("error", "DatabaseManager",
		# 									  "Could not update the Spool, because someone already modified the spool. Do a reload!")
		# 			return

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
				self._logger.exception("Could not insert Spool into database")

				self._passMessageToClient("error", "DatabaseManager", "Could not insert the printjob into the database. See OctoPrint.log for details!")
			pass

		return databaseId


	def loadAllSpoolsByQuery(self, tableQuery):
		if (self._isConnected == False):
			self._logger.error("Database not connected. Check database-settings!")
			return

		if (tableQuery == None):
			return SpoolModel.select().order_by(SpoolModel.created.desc())

		offset = int(tableQuery["from"])
		limit = int(tableQuery["to"])
		sortColumn = tableQuery["sortColumn"]
		sortOrder = tableQuery["sortOrder"]
		filterName = tableQuery["filterName"]

		myQuery = SpoolModel.select().offset(offset).limit(limit)
		if (filterName == "hideEmptySpools"):
			myQuery = myQuery.where( (SpoolModel.remainingWeight > 0) | (SpoolModel.remainingWeight == None))
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
		if ("remaining" == sortColumn):
			if ("desc" == sortOrder):
				myQuery = myQuery.order_by(SpoolModel.remainingWeight.desc())
			else:
				myQuery = myQuery.order_by(SpoolModel.remainingWeight)
		if ("material" == sortColumn):
			if ("desc" == sortOrder):
				myQuery = myQuery.order_by(SpoolModel.material.desc())
			else:
				myQuery = myQuery.order_by(SpoolModel.material)

		return myQuery


	def countSpoolsByQuery(self):
		if (self._isConnected == False):
			self._logger.error("Database not connected. Check database-settings!")
			return

		# filterName = tableQuery["filterName"]

		myQuery = SpoolModel.select()
		# if (filterName == "onlySuccess"):
		# 	myQuery = myQuery.where(PrintJobModel.printStatusResult == "success")
		# elif (filterName == "onlyFailed"):
		# 	myQuery = myQuery.where(PrintJobModel.printStatusResult != "success")

		return myQuery.count()


	def loadCatalogVendors(self, tableQuery):
		if (self._isConnected == False):
			self._logger.error("Database not connected. Check database-settings!")
			return list()

		result = set()
		result.add("")
		myQuery = SpoolModel.select(SpoolModel.vendor).distinct()
		for spool in myQuery:
			value = spool.vendor
			if (value != None):
				result.add(value)
		return result;


	def loadCatalogMaterials(self, tableQuery):
		if (self._isConnected == False):
			self._logger.error("Database not connected. Check database-settings!")
			return list()

		result = set()
		result.add("")
		myQuery = SpoolModel.select(SpoolModel.material).distinct()
		for spool in myQuery:
			value = spool.material
			if (value != None):
				result.add(value)
		return result;


	def loadCatalogLabels(self, tableQuery):
		if (self._isConnected == False):
			self._logger.error("Database not connected. Check database-settings!")
			return list()

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
		if (self._isConnected == False):
			self._logger.error("Database not connected. Check database-settings!")
			return

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

				self._passMessageToClient("Spool-DatabaseManager", "Could not delete the spool ('"+ str(databaseId) +"') from the database. See OctoPrint.log for details!")
			pass
