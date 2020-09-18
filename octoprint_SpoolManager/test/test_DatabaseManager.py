import os
import pprint
import unittest

from octoprint_SpoolManager import DatabaseManager
import logging

from octoprint_SpoolManager.models.SpoolModel import SpoolModel

databaselocation = "/Users/o0632/Library/Application Support/OctoPrint/data/SpoolManager/"

class TestDatabase(unittest.TestCase):

	postgresDatabaseSettings = DatabaseManager.DatabaseSettings()
	postgresDatabaseSettings.useExternal = True
	postgresDatabaseSettings.type = "postgres"
	postgresDatabaseSettings.host = "localhost"
	postgresDatabaseSettings.port = 5432
	postgresDatabaseSettings.name = "spoolmanagerdb"
	postgresDatabaseSettings.user = "Olli"
	postgresDatabaseSettings.password = "illO"


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
		testLogger = logging.getLogger("testLogger")
		logging.info("Start Database-Test")
		self.databaseManager = DatabaseManager(testLogger, True)

		# databaseSettings = {
		# 	"useExternal": "true",
		# 	"type": "postgres",
		# 	"host": "localhost",
		# 	"port": 5432,
		# 	"databaseName": "spoolmanagerdb",
		# 	"user": "Olli",
		# 	"password": "illO"
		# }
		#
		# self.databaseManager.initDatabase(self.databaselocation, databaseSettings, self._clientOutput)

	##################################################################################################   POSTGRES CONNECTION
	def _test_connectToPostgres(self):
		databaseSettings = {
			"useExternal": True,
			"type": "postgres",
			"host": "localhost",
			"port": 5432,
			"databaseName": "spoolmanagerdb",
			"user": "Olli",
			"password": "illO"
		}
		self.databaseManager.initDatabase(self.databaselocation, databaseSettings, self._clientOutput)
		self.assertTrue(self.databaseManager.isConnected(),"No Database connection")

	##################################################################################################   LOCAL CONNECTION
	def _test_connectToLocalSQL3(self):
		databaseSettings = {
			"useExternal": False
		}
		self.databaseManager.initDatabase(self.databaselocation, databaseSettings, self._clientOutput)
		self.assertTrue(self.databaseManager.isConnected(),"No Database connection")

	##################################################################################################   LOAD META DATA
	def _test_readMetadata(self):
		databaseSettings = DatabaseManager.DatabaseSettings()
		databaseSettings.baseFolder = databaselocation

		self.databaseManager.initDatabase( databaseSettings, self._clientOutput)
		metadata = self.databaseManager.loadDatabaseMetaInformations(databaseSettings)
		print(metadata)

	##################################################################################################   CREATE DATABASE
	def _test_createDatabase(self):

		self.databaseManager.initDatabase(self.postgresDatabaseSettings, self._clientOutput)
		self.databaseManager.reCreateDatabase(self.postgresDatabaseSettings)
		metadata = self.databaseManager.loadDatabaseMetaInformations(self.postgresDatabaseSettings)
		print(metadata)

	##################################################################################################   SAVE SPOOL
	def test_createDatabase(self):
		spoolModel = SpoolModel()
		spoolModel.displayName = "Number1"

		self.databaseManager.initDatabase(self.postgresDatabaseSettings, self._clientOutput)
		databaseId = self.databaseManager.saveModel(spoolModel)
		print(databaseId)



if __name__ == '__main__':
	print("Start DatabaseManager Test")
	unittest.main()
	print("Finished")
