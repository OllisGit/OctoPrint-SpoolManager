import os
import pprint
import unittest

from octoprint_SpoolManager import DatabaseManager, SpoolManagerAPI
import logging

from octoprint_SpoolManager.models.SpoolModel import SpoolModel

class TestDatabase(unittest.TestCase):

	sqliteDatabaseSettings = DatabaseManager.DatabaseSettings()
	sqliteDatabaseSettings.useExternal = False
	sqliteDatabaseSettings.baseFolder = "/Users/o0632/Library/Application Support/OctoPrint/data/SpoolManager/"

	postgresDatabaseSettings = DatabaseManager.DatabaseSettings()
	postgresDatabaseSettings.type = "postgres"
	postgresDatabaseSettings.host = "localhost"
	postgresDatabaseSettings.port = 5432
	postgresDatabaseSettings.name = "spoolmanagerdb"
	postgresDatabaseSettings.user = "Olli"
	postgresDatabaseSettings.password = "illO"

	mysqlDatabaseSettings = DatabaseManager.DatabaseSettings()
	mysqlDatabaseSettings.type = "mysql"
	mysqlDatabaseSettings.host = "localhost"
	mysqlDatabaseSettings.port = 3306
	mysqlDatabaseSettings.name = "spoolmanagerdb"
	mysqlDatabaseSettings.user = "Olli"
	mysqlDatabaseSettings.password = "illO"


	def setUp(self):
		self.init_database()

	def _clientOutput(self, type, title, message):
		print("**********************************************")
		print("Type:"+type)
		print("Title:"+title)
		print("Message:"+message)
		print("**********************************************")

	def init_database(self):
		logging.basicConfig(level=logging.DEBUG)
		self.testLogger = logging.getLogger("testLogger")
		logging.info("Start Database-Test")
		self.databaseManager = DatabaseManager(self.testLogger, True)

		# databaseSettings = {
		# 	"type": "postgres",
		# 	"host": "localhost",
		# 	"port": 5432,
		# 	"databaseName": "spoolmanagerdb",
		# 	"user": "Olli",
		# 	"password": "illO"
		# }
		#
		# self.databaseManager.initDatabase(self.databaselocation, databaseSettings, self._clientOutput)

	##################################################################################################   SQLITE CONNECTION
	def _test_connectToSQLite(self):
		self.testLogger.info("--------------------- SQLITE CONNECTION")
		self.databaseManager.initDatabase(self.sqliteDatabaseSettings, self._clientOutput)
		self.assertTrue( self.databaseManager.testDatabaseConnection() == None, "No Database connection")
		self.testLogger.info("--------------------- SQLITE CONNECTION - DONE")

	##################################################################################################   POSTGRES CONNECTION
	def _test_connectToPostgres(self):
		self.testLogger.info("--------------------- POSTGRESS CONNECTION")
		self.databaseManager.initDatabase(self.postgresDatabaseSettings, self._clientOutput)
		self.assertTrue(self.databaseManager.testDatabaseConnection() == None, "No Database connection")
		self.testLogger.info("--------------------- POSTGRESS CONNECTION - DONE")

	##################################################################################################   MYSQL CONNECTION
	def _test_connectToMySQL(self):
		self.testLogger.info("--------------------- MYSQL CONNECTION")
		self.databaseManager.initDatabase(self.mysqlDatabaseSettings, self._clientOutput)
		self.databaseManager.connectoToDatabase()
		self.assertTrue(self.databaseManager.testDatabaseConnection() == None, "No Database connection")
		self.testLogger.info("--------------------- MYSQL CONNECTION - DONE")

	##################################################################################################   LOAD META DATA
	def _test_readMetadata(self):

		self.databaseManager.initDatabase(self.sqliteDatabaseSettings, self._clientOutput)
		# self.databaseManager.initDatabase(self.postgresDatabaseSettings, self._clientOutput)
		# self.databaseManager.initDatabase(self.mysqlDatabaseSettings, self._clientOutput)
		metadata = self.databaseManager.loadDatabaseMetaInformations()
		print(metadata)

	##################################################################################################   CREATE DATABASE
	def _test_createDatabase(self):

		self.databaseManager.initDatabase(self.postgresDatabaseSettings, self._clientOutput)
		self.databaseManager.reCreateDatabase(self.postgresDatabaseSettings)
		metadata = self.databaseManager.loadDatabaseMetaInformations()
		print(metadata)
		allSpoolModels = self.databaseManager.loadAllSpoolsByQuery()
		self.assertEqual( 0, len(allSpoolModels), "Database not reCreated. Still spools inside")

	##################################################################################################   REUSABEL CONNECTION
	def _test_handleReusableConnectionl(self):

		self.databaseManager.initDatabase(self.postgresDatabaseSettings, self._clientOutput)
		self.databaseManager.connectoToDatabase()
		spool = self.databaseManager.loadSpool(1, withReusedConnection=True)
		import time
		time.sleep(3)
		print(spool.displayName)

		allSpoolModels = self.databaseManager.loadAllSpoolsByQuery(withReusedConnection=True)
		print(len(allSpoolModels))
		import time
		time.sleep(3)

		if (allSpoolModels != None):
			for spoolModel in allSpoolModels:
				print(spoolModel.displayName)


		self.databaseManager.closeDatabase()

	##################################################################################################   LOAD SINGLE SPOOL
	def test_loadSingleSpool(self):

		self.databaseManager.initDatabase(self.sqliteDatabaseSettings, self._clientOutput)
		spool = self.databaseManager.loadSpool("9")
		# import time
		# time.sleep(3)
		print(spool.displayName)

	##################################################################################################   LOAD ALL SPOOLS
	def _test_loadAllSpools(self):

		self.databaseManager.initDatabase(self.sqliteDatabaseSettings, self._clientOutput)

		tableQuery = {
			"from": 0,
			"to": 100,
			"sortColumn": "remaining",
			"sortOrder": "asc",
			"filterName": "all",
			"materialFilter": "ABS,PLA",
			"vendorFilter": "all",
			"colorFilter": "#ff0000;red,#ff0000;keinRot"
		}

		allSpoolModels = self.databaseManager.loadAllSpoolsByQuery(tableQuery)
		print(len(allSpoolModels))
		# import time
		# time.sleep(3)

		if (allSpoolModels != None):
			for spoolModel in allSpoolModels:
				displayName = spoolModel.displayName
				remainingWeight = str(spoolModel.remainingWeight)
				color = spoolModel.color + " " + spoolModel.colorName
				material = spoolModel.material
				print("Spool:'"+ displayName + "' Color:'" + color + "' Material:'"+material+"'")

	##################################################################################################   SAVE SPOOL
	def _test_saveSpool(self):
		spoolModel = SpoolModel()
		spoolModel.displayName = "TESTSPOOL - Number1"

		self.databaseManager.initDatabase(self.postgresDatabaseSettings, self._clientOutput)
		databaseId = self.databaseManager.saveSpool(spoolModel)
		print(databaseId)
		self.assertTrue( databaseId != None, "Spool not saved")

		spoolModel = self.databaseManager.loadSpool(databaseId)
		self.assertTrue(spoolModel != None, "Spool not loaded")
		self.assertEqual("TESTSPOOL - Number1", spoolModel.displayName, "Spool not saved")

	##################################################################################################   DELETE SPOOL
	def _test_deleteSpool(self):
		self.databaseManager.initDatabase(self.postgresDatabaseSettings, self._clientOutput)
		databaseId = 3
		print(databaseId)

		deletedDatabaseId = self.databaseManager.deleteSpool(databaseId)
		self.assertEqual(databaseId, deletedDatabaseId, "Spool not deleted")


	##################################################################################################   DELETE SPOOL
	def _test_materialModels(self):
		self.databaseManager.initDatabase(self.sqliteDatabaseSettings, self._clientOutput)



if __name__ == '__main__':
	print("Start DatabaseManager Test")
	unittest.main()
	print("Finished")
