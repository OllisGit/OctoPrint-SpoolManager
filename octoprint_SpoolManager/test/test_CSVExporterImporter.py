import logging

# from octoprint_PrintJobHistory.api import TransformPrintJob2JSON
# from octoprint_PrintJobHistory.common.CSVExportImporter import parseCSV, transform2CSV
#
# logging.basicConfig(level=logging.DEBUG)
# testLogger = logging.getLogger("testLogger")
# logging.info("Start CSV-Test")
# ###################################
# ## IMPORT
#
# def updateParsingStatus(lineNumber):
# 	print("Parsing line '{}'".format(int(lineNumber)))
#
# print("START IMPORT")
# errorCollection = list()
# csvFile4Import = "/Users/o0632/0_Projekte/3DDruck/OctoPrint/OctoPrint-PrintJobHistory/testdata/sample.csv"
# result = parseCSV(csvFile4Import, updateParsingStatus,  errorCollection, testLogger, deleteAfterParsing=False)
# print(errorCollection)
# print("END IMPORT")

#
#
# ###################################
# # EXPORT CSV TEST with single MOCK-Object
# singleJob = {
# 	"userName": "Olaf",
# 	# "printStartDateTimeFormatted": datetime.datetime(2019, 12, 11, 14, 53),
# 	"printStartDateTimeFormatted": "2019-12-11 14:53",
# 	"printStatusResult": "success",
# 	"duration": 0,
# 	"fileSize": 3123,
# 	"temperatureModels": [
# 		{"sensorName": "bed", "sensorValue": 123.3},
# 		{"sensorName": "tool0", "sensorValue": 321.1}
# 	],
# 	"filamentModel": {
# 		"spoolName": "My Best Spool",
# 		"material": "PETG",
# 		"diameter": 1.234,
# 		"density": 1.25,
# 		"usedLengthFormatted": 9.24,
# 		"calculatedLengthFormatted": 100.24,
# 		"usedWeight": 6.06,
# 		"usedCost": 0.04
# 	}
# }

# NOT WORKING
# allJobsModels = list()
# allJobsModels.append(singleJob)
# allJobsDict = TransformPrintJob2JSON.transformAllPrintJobModels(allJobsModels)
# csvResult = transform2CSV(allJobsDict)
#
# print(csvResult)

# from datetime import date
# from datetime import datetime
#
# now = datetime.now()
# # today = date.today()
# print(now.strftime('%I:%M'))
# pass

# from octoprint.plugins.softwareupdate.version_checks import github_release
#
# result = github_release._is_current(dict(
# 										local=dict(value="1.0.0rc6"),
# 										remote=dict(value="1.0.0rc7")),
# 									"python", force_base=False )
# if (result):
# 	print("Locale Version is newer or equal")
# else:
# 	print("Remote Version is newer, update available")


# f = open("costUnitBug.txt", "r")
# fieldValue = f.readline()
# f.close()
# fieldValue = fieldValue.strip()
# costUnit = fieldValue[-1]
# if (costUnit.isdigit()):
# 	# no unit present
# 	usedCost = float(fieldValue)
# else:
# 	# Split between cot and unit
# 	costValue = ""
# 	for i in range(len(fieldValue)):
# 		c = fieldValue[i]
# 		if (c.isdigit() or c == "." ):
# 			costValue += c
# 		else:
# 			costUnit = fieldValue[i:]
# 			break
#
# print(usedCost)
# print(costUnit)
