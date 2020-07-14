from octoprint_SpoolManager import DatabaseManager
import logging

databaselocation = "/Users/o0632/Library/Application Support/OctoPrint/data/SpoolManager/"

def clientOutput(message1, message2):
	print(message1)
	print(message2)

logging.basicConfig(level=logging.DEBUG)
testLogger = logging.getLogger("testLogger")
logging.info("Start Database-Test")
databaseManager = DatabaseManager(testLogger)
databaseManager.initDatabase(databaselocation, clientOutput)


# result = databaseManager.loadCatalogVendors(None)
# print (result)
#
# result = databaseManager.loadCatalogMaterials(None)
# print (result)
#
# result = databaseManager.loadCatalogLabels(None)
# print (result)

result = databaseManager.loadSpoolTemplateSpool()
print (list(result))
# for spool in result:
#     print(spool.displayName)


# result = databaseManager.loadSpool(1)
# print (result.displayName)
# print (result)
