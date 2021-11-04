# coding=utf-8

import io
from io import StringIO
import csv
import datetime
import os
import re

from octoprint_SpoolManager.common import StringUtils
from octoprint_SpoolManager.models.SpoolModel import SpoolModel

FORMAT_DATETIME = "%d.%m.%Y %H:%M"
FORMAT_DATE = "%d.%m.%Y"

COLUMN_DISPLAY_NAME = "Spool Name"
COLUMN_COLOR_NAME = "Color Name"
COLUMN_COLOR_CODE = "Color Code [hex]"
COLUMN_VENDOR = "Vendor"
COLUMN_MATERIAL = "Material"
COLUMN_SERIALNUMBER = "Serialnumber"
COLUMN_DENSITY = "Density [g/cm3]"
COLUMN_DIAMETER = "Diameter [mm]"
COLUMN_DIAMETER_TOLERANCE = "Diameter Tolerance[mm]"
COLUMN_FLOWRATECOMPENSATION = "Flow rate compensation [%]"
COLUMN_TEMPERATURE = "Temperature [C]"
COLUMN_TEMPERATURE_BED = "Bed Temperature [C]"
COLUMN_TEMPERATURE_ENCLOSURE = "Enclosure Temperature [C]"
COLUMN_OFFSET_TEMPERATURE = "Offset Temperature [C]"
COLUMN_OFFSET_TEMPERATURE_BED = "Offset Bed Temperature [C]"
COLUMN_OFFSET_TEMPERATURE_ENCLOSURE = "Offset Enclosure Temperature [C]"
COLUMN_TOTAL_WEIGHT = "Total weight [g]"
COLUMN_SPOOL_WEIGHT = "Spool weight [g]"
COLUMN_USED_WEIGHT = "Used weight [g]"
COLUMN_TOTAL_LENGTH = "Total length [mm]"
COLUMN_USED_LENGTH = "Used length [mm]"
COLUMN_FIST_USE_DATETIME = "First use [dd.mm.yyyy hh:mm]"
COLUMN_LAST_USE_DATETIME = "Last use [dd.mm.yyyy hh:mm]"
COLUMN_PURCHASED_FROM = "Purchased from"
COLUMN_PURCHASED_DATE = "Purchased on [dd.mm.yyyy]"
COLUMN_COST = "Cost"
COLUMN_COST_UNIT = "Cost unit"
COLUMN_NOTE = "Note"

#############################################################################################################
class CSVColumn:
	fieldName = ""
	columnLabel = ""
	description = ""
	formattorParser = None

	def __init__(self, fieldName, columnLabel, description, formattorParser):
		self.fieldName = fieldName
		self.columnLabel = columnLabel
		self.description = description
		self.formattorParser = formattorParser

	def getCSV(self, spoolModel):
		columnValue =  self.formattorParser.formatValue(spoolModel, self.fieldName)

		columnValue = StringUtils.to_native_str(columnValue)

		return columnValue

	def parseAndAssignFieldValue(self, fieldValue, printJobModel, errorCollection, lineNumber):
		try:
			self.formattorParser.parseAndAssignFieldValue(self.columnLabel, self.fieldName, fieldValue, printJobModel, errorCollection, lineNumber)
		except Exception as e:
			errorMessage = str(e)
			errorMessage = re.sub(r"[^a-zA-Z0-9()]"," ", errorMessage) # fix for: #32 'invalid literal for float(): 0.00 <k> '
			errorCollection.append("[" + str(
				lineNumber) + "]" + "Error parsing value '" + fieldValue + "' for field '" + self.columnLabel + "': " + errorMessage)


############################################################################################## ALL FORMATTOR AND PARSERS

class DefaultCSVFormattorParser:

	def formatValue(self, printJob, fieldName):
		if (hasattr(printJob, fieldName) == False):
			return "-"
		valueToFormat = getattr(printJob, fieldName)

		adjustedValue = valueToFormat if valueToFormat is not None else '-'
		if (type(adjustedValue) is int or type(adjustedValue) is float or type(adjustedValue) is str or type(adjustedValue) is unicode):
			adjustedValue = StringUtils.to_native_str(adjustedValue)
			adjustedValue = adjustedValue.replace('\n', ' ').replace('\r', '')
		else:
			# print("BOOOOOOMMMMM!!!!!  "+str(type(adjustedValue)))
			adjustedValue = "#"		# workaround to identify not correct mapped values
		return adjustedValue

	def parseAndAssignFieldValue(self, fieldLabel, fieldName, fieldValue, printJobModel, errorCollection, lineNumber):
		if ("" == fieldValue or "-" == fieldValue or fieldValue == None):
			# check if mandatory
			return

		# TODO custom color-code parser: rules all lowercase and #fff == #ffffff
		if ("color" == fieldName):
			fieldValue = fieldValue.lower()

		setattr(printJobModel, fieldName, fieldValue)

class DateTimeCSVFormattorParser:

	def formatValue(self, printJob, fieldName):
		if (hasattr(printJob, fieldName) == False):
			return "-"
		valueToFormat = getattr(printJob, fieldName)

		if valueToFormat is None or "" == valueToFormat:
			return "-"
		adjustedValue = valueToFormat.strftime(FORMAT_DATETIME)
		valueToFormat = adjustedValue
		return valueToFormat

	def parseAndAssignFieldValue(self, fieldLabel, fieldName, fieldValue, printJobModel, errorCollection, lineNumber):
		if ("" == fieldValue or "-" == fieldValue or fieldValue == None):
			# check if mandatory
			return
		if (":" in fieldValue):
			# looks like timestamp in format 19.12.2019 10:07
			fieldDateTime = datetime.datetime.strptime(fieldValue, FORMAT_DATETIME)
			setattr(printJobModel, fieldName, fieldDateTime)
			pass
		else:
			fieldDateTime = datetime.datetime.strptime(fieldValue, FORMAT_DATE)
			setattr(printJobModel, fieldName, fieldDateTime)
			pass
		pass

class NumberCSVFormattorParser:

	def formatValue(self, printJob, fieldName):
		if (hasattr(printJob, fieldName) == False):
			return "-"
		valueToFormat = getattr(printJob, fieldName)

		adjustedValue = valueToFormat if valueToFormat is not None else '-'
		if (type(adjustedValue) is int or type(adjustedValue) is float or type(adjustedValue) is str or type(adjustedValue) is unicode):
			adjustedValue = StringUtils.to_native_str(adjustedValue)
			adjustedValue = adjustedValue.replace('\n', ' ').replace('\r', '')
		else:
			adjustedValue = "#"		# workaround to identify not correct mapped values
		return adjustedValue

	def parseAndAssignFieldValue(self, fieldLabel, fieldName, fieldValue, spoolModel, errorCollection, lineNumber):
		if ("" == fieldValue or "-" == fieldValue or fieldValue == None):
			# check if mandatory
			return

		if ("density" == fieldName):
			fieldValue = float(fieldValue)
		if ("diameter" == fieldName):
			fieldValue = float(fieldValue)
		if ("diameterTolerance" == fieldName):
			fieldValue = float(fieldValue)
		if ("flowRateCompensation" == fieldName):
			fieldValue = int(fieldValue)
		if ("temperature" == fieldName):
			fieldValue = int(fieldValue)
		if ("bedTemperature" == fieldName):
			fieldValue = int(fieldValue)
		if ("enclosureTemperature" == fieldName):
			fieldValue = int(fieldValue)
		if ("offsetTemperature" == fieldName):
			fieldValue = int(fieldValue)
		if ("offsetBedTemperature" == fieldName):
			fieldValue = int(fieldValue)
		if ("offsetEnclosureTemperature" == fieldName):
			fieldValue = int(fieldValue)
		if ("totalWeight" == fieldName):
			fieldValue = float(fieldValue)
		if ("spoolWeight" == fieldName):
			fieldValue = float(fieldValue)
		if ("usedWeight" == fieldName):
			fieldValue = float(fieldValue)
		if ("totalLength" == fieldName):
			fieldValue = int(fieldValue)
		if ("usedLength" == fieldName):
			fieldValue = int(fieldValue)
		if ("cost" == fieldName):
			fieldValue = float(fieldValue)

		setattr(spoolModel, fieldName, fieldValue)

######################################################################################################################
## CSV HEADER-ORDER
ALL_COLUMNS_SORTED = [
	COLUMN_DISPLAY_NAME,
	COLUMN_COLOR_NAME,
	COLUMN_COLOR_CODE,
	COLUMN_VENDOR,
	COLUMN_MATERIAL,
	COLUMN_SERIALNUMBER,
	COLUMN_DENSITY,
	COLUMN_DIAMETER,
	COLUMN_DIAMETER_TOLERANCE,
	COLUMN_FLOWRATECOMPENSATION,
	COLUMN_TEMPERATURE,
	COLUMN_TEMPERATURE_BED,
	COLUMN_TEMPERATURE_ENCLOSURE,
	COLUMN_OFFSET_TEMPERATURE,
	COLUMN_OFFSET_TEMPERATURE_BED,
	COLUMN_OFFSET_TEMPERATURE_ENCLOSURE,
	COLUMN_TOTAL_WEIGHT,
	COLUMN_SPOOL_WEIGHT,
	COLUMN_USED_WEIGHT,
	COLUMN_TOTAL_LENGTH,
	COLUMN_USED_LENGTH,
	COLUMN_FIST_USE_DATETIME,
	COLUMN_LAST_USE_DATETIME,
	COLUMN_PURCHASED_FROM,
	COLUMN_PURCHASED_DATE,
	COLUMN_COST,
	COLUMN_COST_UNIT,
	COLUMN_NOTE
]

## ALL COLUMNS WITH THERE PARSER/EXPORTER
ALL_COLUMNS = {
	COLUMN_DISPLAY_NAME: CSVColumn("displayName", COLUMN_DISPLAY_NAME, "", DefaultCSVFormattorParser()),
	COLUMN_COLOR_NAME: CSVColumn("colorName", COLUMN_COLOR_NAME, "", DefaultCSVFormattorParser()),
	COLUMN_COLOR_CODE: CSVColumn("color", COLUMN_COLOR_CODE, "", DefaultCSVFormattorParser()),
	COLUMN_VENDOR: CSVColumn("vendor", COLUMN_VENDOR, "", DefaultCSVFormattorParser()),
	COLUMN_MATERIAL: CSVColumn("material", COLUMN_MATERIAL, "", DefaultCSVFormattorParser()),
	COLUMN_SERIALNUMBER: CSVColumn("code", COLUMN_SERIALNUMBER, "", DefaultCSVFormattorParser()),
	COLUMN_DENSITY: CSVColumn("density", COLUMN_DENSITY, "", NumberCSVFormattorParser()),
	COLUMN_DIAMETER: CSVColumn("diameter", COLUMN_DIAMETER, "", NumberCSVFormattorParser()),
	COLUMN_DIAMETER_TOLERANCE: CSVColumn("diameterTolerance", COLUMN_DIAMETER_TOLERANCE, "", NumberCSVFormattorParser()),
	COLUMN_FLOWRATECOMPENSATION: CSVColumn("flowRateCompensation", COLUMN_FLOWRATECOMPENSATION, "", NumberCSVFormattorParser()),
	COLUMN_TEMPERATURE: CSVColumn("temperature", COLUMN_TEMPERATURE, "", NumberCSVFormattorParser()),
	COLUMN_TEMPERATURE_BED: CSVColumn("bedTemperature", COLUMN_TEMPERATURE_BED, "", NumberCSVFormattorParser()),
	COLUMN_TEMPERATURE_ENCLOSURE: CSVColumn("enclosureTemperature", COLUMN_TEMPERATURE_ENCLOSURE, "", NumberCSVFormattorParser()),
	COLUMN_OFFSET_TEMPERATURE: CSVColumn("offsetTemperature", COLUMN_OFFSET_TEMPERATURE, "", NumberCSVFormattorParser()),
	COLUMN_OFFSET_TEMPERATURE_BED: CSVColumn("offsetBedTemperature", COLUMN_OFFSET_TEMPERATURE_BED, "", NumberCSVFormattorParser()),
	COLUMN_OFFSET_TEMPERATURE_ENCLOSURE: CSVColumn("offsetEnclosureTemperature", COLUMN_OFFSET_TEMPERATURE_ENCLOSURE, "", NumberCSVFormattorParser()),
	COLUMN_TOTAL_WEIGHT: CSVColumn("totalWeight", COLUMN_TOTAL_WEIGHT, "", NumberCSVFormattorParser()),
	COLUMN_SPOOL_WEIGHT: CSVColumn("spoolWeight", COLUMN_SPOOL_WEIGHT, "", NumberCSVFormattorParser()),
	COLUMN_USED_WEIGHT: CSVColumn("usedWeight", COLUMN_USED_WEIGHT, "", NumberCSVFormattorParser()),
	COLUMN_TOTAL_LENGTH: CSVColumn("totalLength", COLUMN_TOTAL_LENGTH, "", NumberCSVFormattorParser()),
	COLUMN_USED_LENGTH: CSVColumn("usedLength", COLUMN_USED_LENGTH, "", NumberCSVFormattorParser()),
	COLUMN_FIST_USE_DATETIME: CSVColumn("firstUse", COLUMN_FIST_USE_DATETIME, "", DateTimeCSVFormattorParser()),
	COLUMN_LAST_USE_DATETIME: CSVColumn("lastUse", COLUMN_LAST_USE_DATETIME, "", DateTimeCSVFormattorParser()),
	COLUMN_PURCHASED_FROM: CSVColumn("purchasedFrom", COLUMN_PURCHASED_FROM, "", DefaultCSVFormattorParser()),
	COLUMN_PURCHASED_DATE: CSVColumn("purchasedOn", COLUMN_PURCHASED_DATE, "", DateTimeCSVFormattorParser()),
	COLUMN_COST: CSVColumn("cost", COLUMN_COST, "", NumberCSVFormattorParser()),
	COLUMN_COST_UNIT: CSVColumn("costUnit", COLUMN_COST_UNIT, "", DefaultCSVFormattorParser()),
	COLUMN_NOTE: CSVColumn("noteText", COLUMN_NOTE, "", DefaultCSVFormattorParser()),
}



####################################################################################################### -> EXPORT TO CSV

def transform2CSV(allJobs):
	result = None
	si = StringIO()	#TODO maybe a bad idea to use a internal memory based string, needs to be switched to response stream
	# si = io.BytesIO()

	writer = csv.writer(si, quoting=csv.QUOTE_ALL)
	#  Write HEADER
	headerList = list()
	csvLine = ""
	for columnKey in ALL_COLUMNS_SORTED:
		csvColumn = ALL_COLUMNS[columnKey]
		label = '"' + csvColumn.columnLabel + '"'
		headerList.append(label)

	csvLine =  "," .join(headerList) + "\n"
	# writer.writerow(headerList)
	# print(csvLine)
	yield csvLine

	# Write CSV-Content
	if (allJobs != None):
		for job in allJobs:
			csvRow = list()
			for columnKey in ALL_COLUMNS_SORTED:
				# print(columnKey)
				csvColumn = ALL_COLUMNS[columnKey]
				csvColumnValue = '"' + csvColumn.getCSV(job)  + '"'
				csvRow.append(csvColumnValue)
			csvLine = ",".join(csvRow) + "\n"
			# print(csvLine)
			yield csvLine
			# writer.writerow(csvRow)
	# result = si.getvalue()
	# return result


########################################################################################################## -> IMPORT CSV
mandatoryFieldNames = [
	ALL_COLUMNS[COLUMN_DISPLAY_NAME].columnLabel,
	# ALL_COLUMNS[COLUMN_FILE_NAME].columnLabel,
	# ALL_COLUMNS[COLUMN_START_DATETIME].columnLabel,
	# ALL_COLUMNS[COLUMN_DURATION].columnLabel,
]

# mandatoryFieldAvaiable = list()

columnOrderInFile = dict()

def parseCSV(csvFile4Import, updateParsingStatus, errorCollection, logger, deleteAfterParsing=True):

	result = list()	# List with printJobModels
	lineNumber = 0
	try:
		with open(csvFile4Import) as csv_file:
			csv_reader = csv.reader(csv_file, delimiter=',')
			lineNumber = 0
			for row in csv_reader:
				lineNumber += 1

				# import time
				# time.sleep(1)
				updateParsingStatus(str(lineNumber))

				if lineNumber == 1:
					# createColumnOrderFromHeader(row)
					# mandatoryFieldCount = 0
					mandatoryFieldAvaiable = list()
					columnIndex = 0
					for column in row:
						column = column.strip()
						if column in ALL_COLUMNS:
							columnOrderInFile[columnIndex] = ALL_COLUMNS[column]
							if column in mandatoryFieldNames:
								mandatoryFieldAvaiable.append(column)
								# mandatoryFieldCount += 1
						columnIndex += 1
					if len(mandatoryFieldAvaiable) != len(mandatoryFieldNames):
					# if mandatoryFieldCount != len(mandatoryFieldNames):
						# identify missing files
						# mandatoryFieldMissing = mandatoryFieldNames - mandatoryFieldAvaiable
						mandatoryFieldMissing = list( set(mandatoryFieldNames) - set(mandatoryFieldAvaiable) )
						errorCollection.append("Mandatory column is missing! <br/><b>'" + "".join(mandatoryFieldMissing) + "'</b><br/>")
						break
				else:
					spoolModel = SpoolModel()
					# parse line with header defined order
					columnIndex = 0
					for columnValue in row:
						if columnIndex in columnOrderInFile:
							csvColumn = columnOrderInFile[columnIndex]
							if not csvColumn == None:
								columnValue = columnValue.strip()
								# check if mandatory value is missing
								if (len(columnValue) == 0):
									columnName = csvColumn.columnLabel
									if columnName in mandatoryFieldNames:
										errorCollection.append("["+str(lineNumber)+"] Mandatory value for column '" + columnName + "' is missing!")
										pass
								else:
									csvColumn.parseAndAssignFieldValue(columnValue, spoolModel, errorCollection, lineNumber)
								pass
						columnIndex += 1
					if (len(errorCollection) != 0):
						logger.error("Reading error line '" + str(lineNumber) + "' in Column '" + column + "' ")
					else:
						result.append(spoolModel)
			pass
	except Exception as e:
		errorMessage = "CSV Parsing error. Line:'" + str(lineNumber) + "' Error:'" + str(e) + "' File:'" + csvFile4Import + "'"
		errorCollection.append(errorMessage)
		logger.error(errorMessage)
	finally:
		if (deleteAfterParsing):
			logger.info("Removing uploded csv temp-file")
			try:
				os.remove(csvFile4Import)
			except Exception:
				pass
	return result

######################################################################################################## -> SAMPLE SPOOL
def createSampleSpoolModel():
	#DisplayName, Vendor, Material, Color[# code], Diameter [mm], Density [g/cm³], Temperature [°C], TotalWeight [g], UsedWeight [g], UsedLength [mm], FirstUse [dd.mm.yyyy hh:mm], LastUse [dd.mm.yyyy hh:mm], PurchasedFrom, PurchasedOn [dd.mm.yyyy hh:mm], Cost, CostUnit, Labels, NoteText

	s1 = SpoolModel()
	s1.displayName = "Sample Spool #1"
	s1.colorName = "raw-red"
	s1.color = "#FF0000"
	s1.vendor = "The Spool Company"
	s1.material = "PETG"
	s1.code = "X000SKGR05"
	s1.diameter = 1.75
	s1.diameterTolerance = 0.2
	s1.density = 1.27
	s1.flowRateCompensation = 110
	s1.temperature = 182
	s1.bedtemperature = 52
	s1.enclosureTemperature = 23
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
