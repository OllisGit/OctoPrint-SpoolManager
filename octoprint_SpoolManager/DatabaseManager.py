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

		def isExternal(self):
			return self.type != "sqlite"

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
	# "type": "postgres",
	# "host": "localhost",
	# "port": 5432,
	# "databaseName": "SpoolManagerDatabase",
	# "user": "Olli",
	# "password": "illO"

	def _buildDatabaseConnection(self):
		database = None
		if (self._databaseSettings.isExternal() == False):
			# local database`
			database = SqliteDatabase(self._databaseSettings.fileLocation)
		else:
			databaseType = self._databaseSettings.type
			databaseName = self._databaseSettings.name
			host = self._databaseSettings.host
			port = self._databaseSettings.port
			user = self._databaseSettings.user
			password = self._databaseSettings.password
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

	def _createDatabase(self, forceCreateTables):

		if forceCreateTables:
			self._logger.info("Creating new database-tables, because FORCE == TRUE!")
			self._createDatabaseTables()
		else:
			# check, if we need an scheme upgrade
			self._createOrUpgradeSchemeIfNecessary()

		self._logger.info("Database created-check done")

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
				"does not exist" in errorMessage or
				# - mySQL errorcode=1146
				"doesn\'t exist" in errorMessage
			):
				self._createDatabaseTables()
				return
			else:
				self._logger.error(str(e))

		if not schemeVersionFromDatabaseModel == None:
			currentDatabaseSchemeVersion = int(schemeVersionFromDatabaseModel.value)
			if (currentDatabaseSchemeVersion < CURRENT_DATABASE_SCHEME_VERSION):
				# auto upgrade done only for local database
				if (self._databaseSettings.isExternal() == True):
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
		else:
			self._logger.warn("...something was strange. Should not be shwon in log. Check full log")
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

		connected = self.connectoToDatabase(sendErrorPopUp=False)
		if (connected == True):
			self._createDatabase(FORCE_CREATE_TABLES)
			self.closeDatabase()

		return self._currentErrorMessageDict

	def assignNewDatabaseSettings(self, databaseSettings):
		self._databaseSettings = databaseSettings

	def testDatabaseConnection(self, databaseSettings = None):
		result = None
		backupCurrentDatabaseSettings = None
		try:
			# use provided databasesettings or default if not provided
			if (databaseSettings != None):
				backupCurrentDatabaseSettings = self._databaseSettings
				self._databaseSettings = databaseSettings

			succesfull = self.connectoToDatabase()
			if (succesfull == False):
				result = self.getCurrentErrorMessageDict()
		finally:
			try:
				self.closeDatabase()
			except:
				pass # do nothing
			self._databaseSettings = backupCurrentDatabaseSettings

		return result


	def getCurrentErrorMessageDict(self):
		return self._currentErrorMessageDict

	# connect to the current database
	def connectoToDatabase(self, withMetaCheck=False, sendErrorPopUp=True) :
		# reset current errorDict
		self._currentErrorMessageDict = None
		self._isConnected = False

		# build connection
		try:
			self._logger.info("Databaseconnection with...")
			self._logger.info(self._databaseSettings)
			self._database = self._buildDatabaseConnection()

			# connect to Database
			DatabaseManager.db = self._database
			self._database.bind(MODELS)

			self._database.connect()
			self._logger.info("Database connection succesful. Checking Scheme versions")
			# TODO do I realy need to check the meta-infos in the connect function
			# schemeVersionFromPlugin = str(CURRENT_DATABASE_SCHEME_VERSION)
			# schemeVersionFromDatabaseModel = str(PluginMetaDataModel.get(PluginMetaDataModel.key == PluginMetaDataModel.KEY_DATABASE_SCHEME_VERSION).value)
			# if (schemeVersionFromPlugin != schemeVersionFromDatabaseModel):
			# 	errorMessage = "Plugin needs database scheme version: "+str(schemeVersionFromPlugin)+", but database has version: "+str(schemeVersionFromDatabaseModel);
			# 	self._storeErrorMessage("error", "database scheme version", errorMessage , False)
			# 	self._logger.error(errorMessage)
			# 	self._isConnected = False
			# else:
			# 	self._logger.info("...succesfull connected")
			# 	self._isConnected = True
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

		backupCurrentDatabaseSettings = None
		if (databaseSettings != None):
			backupCurrentDatabaseSettings = self._databaseSettings
			self._databaseSettings = databaseSettings
		try:
			# - connect to dataabase
			self.connectoToDatabase()

			self._createDatabase(True)

			# - close dataabase
			self.closeDatabase()
		finally:
			# - restore database settings
			if (backupCurrentDatabaseSettings != None):
				self._databaseSettings = backupCurrentDatabaseSettings





	################################################################################################ DATABASE OPERATIONS
	def loadDatabaseMetaInformations(self, databaseSettings = None):

		backupCurrentDatabaseSettings = None
		if (databaseSettings != None):
			backupCurrentDatabaseSettings = self._databaseSettings
		else:
			databaseSettings = self._databaseSettings
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
		loadResult = False
		# - save current DatbaseSettings
		# currentDatabaseSettings = self._databaseSettings
		# currentDatabase = self._database
		# externalConnected = False
		# always read local meta data
		try:
			# First load mete from local sqlite database
			currentDatabaseType = databaseSettings.type
			databaseSettings.type = "sqlite"
			databaseSettings.baseFolder = self._databaseSettings.baseFolder
			databaseSettings.fileLocation = self._databaseSettings.fileLocation
			self._databaseSettings = databaseSettings

			self.connectoToDatabase( sendErrorPopUp=False)
			localSchemeVersionFromDatabaseModel = PluginMetaDataModel.get(PluginMetaDataModel.key == PluginMetaDataModel.KEY_DATABASE_SCHEME_VERSION).value
			localSpoolItemCount = self.countSpoolsByQuery()
			self.closeDatabase()

			# Use orign Databasetype to collect the other meta dtaa (if neeeded)
			databaseSettings.type = currentDatabaseType
			if (databaseSettings.isExternal() == True):
				# External DB
				self._databaseSettings = databaseSettings
				self.connectoToDatabase(sendErrorPopUp=False)
				externalSchemeVersionFromDatabaseModel = PluginMetaDataModel.get(PluginMetaDataModel.key == PluginMetaDataModel.KEY_DATABASE_SCHEME_VERSION).value
				externalSpoolItemCount = self.countSpoolsByQuery()
				self.closeDatabase()
			loadResult = True
		except Exception as e:
			errorMessage = str(e)
			self._logger.exception(e)
			try:
				self.closeDatabase()
			except Exception:
				pass #ignore close exception
		finally:
			# restore orig. databasettings
			if (backupCurrentDatabaseSettings != None):
				self._databaseSettings = backupCurrentDatabaseSettings

		return {
			"success": loadResult,
			"errorMessage": errorMessage,
			"schemeVersionFromPlugin": schemeVersionFromPlugin,
			"localSchemeVersionFromDatabaseModel": localSchemeVersionFromDatabaseModel,
			"localSpoolItemCount": localSpoolItemCount,
			"externalSchemeVersionFromDatabaseModel": externalSchemeVersionFromDatabaseModel,
			"externalSpoolItemCount": externalSpoolItemCount
		}


	def loadSpool(self, databaseId, withReusedConnection=False):
		try:
			if (withReusedConnection == True):
				if (self._isConnected == False):
					self._logger.error("Database not connected. Check database-settings!")
					return
			else:
				self.connectoToDatabase()
			return SpoolModel.get_by_id(databaseId)
		except Exception as e:
			self._logger.exception("Could not load Spool from database")

			self._passMessageToClient("error", "DatabaseManager",
									  "Could not load Spool from database. See OctoPrint.log for details!")
			return None
		finally:
			try:
				if (withReusedConnection == False):
					self._closeDatabase()
			except:
				pass # do nothing
		pass


	def loadSpoolTemplate(self, withReusedConnection=False):
		try:
			if (withReusedConnection == True):
				if (self._isConnected == False):
					self._logger.error("Database not connected. Check database-settings!")
					return
			else:
				self.connectoToDatabase()
			return SpoolModel.select().where(SpoolModel.isTemplate == True)
		except Exception as e:
			self._logger.exception("Could not load SpoolTemplate from database")

			self._passMessageToClient("error", "DatabaseManager",
									  "Could not load SpoolTemplate from database. See OctoPrint.log for details!")
			return None
		finally:
			try:
				if(withReusedConnection == False):
					self._closeDatabase()
			except:
				pass # do nothing
		pass


	def loadAllSpoolsByQuery(self, tableQuery = None, withReusedConnection = False):
		try:
			if (withReusedConnection == True):
				if (self._isConnected == False):
					self._logger.error("Database not connected. Check database-settings!")
					return
			else:
				self.connectoToDatabase()

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

		except Exception as e:
			self._logger.exception("Could not load loadAllSpoolsByQuery from database")

			self._passMessageToClient("error", "DatabaseManager",
									  "Could not loadAllSpoolsByQuery from database. See OctoPrint.log for details!")
			return None
		finally:
			try:
				if(withReusedConnection == False):
					self._closeDatabase()
			except:
				pass  # do nothing
		pass

	def saveSpool(self, spoolModel, withReusedConnection=False):

		try:
			if (withReusedConnection == True):
				if (self._isConnected == False):
					self._logger.error("Database not connected. Check database-settings!")
					return None
			else:
				self.connectoToDatabase()

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
					if (spoolModel.isTemplate == True):
						#  remove template flag from last templateSpool
						SpoolModel.update({SpoolModel.isTemplate: False}).where(SpoolModel.isTemplate == True).execute()

					spoolModel.save()
					databaseId = spoolModel.get_id()
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
		except Exception as e:
			self._logger.exception("Could not load saveModel from database")

			self._passMessageToClient("error", "DatabaseManager",
									  "Could not load saveModel from database. See OctoPrint.log for details!")
			return None
		finally:
			try:
				if(withReusedConnection == False):
					self._closeDatabase()
			except:
				pass # do nothing
		pass


	def countSpoolsByQuery(self, withReusedConnection=False):
		try:
			if (withReusedConnection == True):
				if (self._isConnected == False):
					self._logger.error("Database not connected. Check database-settings!")
					return None
			else:
				self.connectoToDatabase()

			myQuery = SpoolModel.select()

			return myQuery.count()
		except Exception as e:
			self._logger.exception("Could not load countSpoolsByQuery from database")

			self._passMessageToClient("error", "DatabaseManager",
									  "Could not load countSpoolsByQuery from database. See OctoPrint.log for details!")
			return None
		finally:
			try:
				if (withReusedConnection == False):
					self._closeDatabase()
			except:
				pass # do nothing
		pass


	def loadCatalogVendors(self, tableQuery, withReusedConnection=False):
		try:
			if (withReusedConnection == True):
				if (self._isConnected == False):
					self._logger.error("Database not connected. Check database-settings!")
					return set()
			else:
				self.connectoToDatabase()

			result = set()
			result.add("")
			myQuery = SpoolModel.select(SpoolModel.vendor).distinct()
			for spool in myQuery:
				value = spool.vendor
				if (value != None):
					result.add(value)
			return result;
		except Exception as e:
			self._logger.exception("Could not load loadCatalogVendors from database")

			self._passMessageToClient("error", "DatabaseManager",
									  "Could not load loadCatalogVendors from database. See OctoPrint.log for details!")
			return None
		finally:
			try:
				if (withReusedConnection == False):
					self._closeDatabase()
			except:
				pass # do nothing
		pass


	def loadCatalogMaterials(self, tableQuery, withReusedConnection=False):
		try:
			if (withReusedConnection == True):
				if (self._isConnected == False):
					self._logger.error("Database not connected. Check database-settings!")
					return set()
			else:
				self.connectoToDatabase()

			result = set()
			result.add("")
			myQuery = SpoolModel.select(SpoolModel.material).distinct()
			for spool in myQuery:
				value = spool.material
				if (value != None):
					result.add(value)
			return result;
		except Exception as e:
			self._logger.exception("Could not load SpoolTemplate from database")

			self._passMessageToClient("error", "DatabaseManager",
									  "Could not load SpoolTemplate from database. See OctoPrint.log for details!")
			return None
		finally:
			try:
				if (withReusedConnection == False):
					self._closeDatabase()
			except:
				pass # do nothing
		pass


	def loadCatalogLabels(self, tableQuery, withReusedConnection=False):
		try:
			if (withReusedConnection == True):
				if (self._isConnected == False):
					self._logger.error("Database not connected. Check database-settings!")
					return set()
			else:
				self.connectoToDatabase()

			result = set()
			result.add("")
			myQuery = SpoolModel.select(SpoolModel.labels).distinct()
			for spool in myQuery:
				value = spool.labels
				if (value != None):
					spoolLabels = json.loads(value)
					for singleLabel in spoolLabels:
						result.add(singleLabel)
			return result
		except Exception as e:
			self._logger.exception("Could not load loadCatalogLabels from database")

			self._passMessageToClient("error", "DatabaseManager",
									  "Could not load loadCatalogLabels from database. See OctoPrint.log for details!")
			return None
		finally:
			try:
				if (withReusedConnection == False):
					self._closeDatabase()
			except:
				pass # do nothing
		pass


	def deleteSpool(self, databaseId, withReusedConnection=False):
		try:
			if (withReusedConnection == True):
				if (self._isConnected == False):
					self._logger.error("Database not connected. Check database-settings!")
					return None
			else:
				self.connectoToDatabase()

			with self._database.atomic() as transaction:  # Opens new transaction.
				try:
					# first delete relations
					# n = FilamentModel.delete().where(FilamentModel.printJob == databaseId).execute()
					# n = TemperatureModel.delete().where(TemperatureModel.printJob == databaseId).execute()

					deleteResult = SpoolModel.delete_by_id(databaseId)
					if (deleteResult == 0):
						return None
					pass
				except Exception as e:
					# Because this block of code is wrapped with "atomic", a
					# new transaction will begin automatically after the call
					# to rollback().
					transaction.rollback()
					self._logger.exception("Could not delete spool from database:" + str(e))

					self._passMessageToClient("Spool-DatabaseManager", "Could not delete the spool ('"+ str(databaseId) +"') from the database. See OctoPrint.log for details!")
					return None
				pass
		except Exception as e:
			self._logger.exception("Could not load deleteSpool from database")

			self._passMessageToClient("error", "DatabaseManager",
									  "Could not load deleteSpool from database. See OctoPrint.log for details!")
			return None
		finally:
			try:
				if (withReusedConnection == False):
					self._closeDatabase()
			except:
				pass # do nothing
		# success, return databaseId
		return databaseId
