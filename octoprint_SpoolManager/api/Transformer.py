# coding=utf-8
from __future__ import absolute_import

from octoprint_SpoolManager.models.SpoolModel import SpoolModel
from octoprint_SpoolManager.common import StringUtils

def calculateRemainingWeight(usedWeight, totalWeight):
	if (usedWeight == None or totalWeight == None):
		return None

	if ( (type(usedWeight) == int or type(usedWeight) == float) and
			(type(totalWeight) == int or type(totalWeight) == float) ):
		result = totalWeight - usedWeight
		return result

	return None

def _calculateRemainingPercentage(remainingWeight, totalWeight):
	if (remainingWeight == None or totalWeight == None):
		return None

	if ( (type(remainingWeight) == int or type(remainingWeight) == float) and
			(type(totalWeight) == int or type(totalWeight) == float) ):
		result = remainingWeight / (totalWeight / 100.0);
		return result

	return None

def _calculateUsedPercentage(usedWeight, totalWeight):
	if (usedWeight == None or totalWeight == None):
		return None

	if ( (type(usedWeight) == int or type(usedWeight) == float) and
			(type(totalWeight) == int or type(totalWeight) == float) ):
		result = usedWeight / (totalWeight / 100.0);
		return result

	return None


def transformSpoolModelToDict(spoolModel):
	spoolAsDict = spoolModel.__data__

	# Date time needs to be converted
	spoolAsDict["firstUse"] = StringUtils.formatDateTime(spoolModel.firstUse)
	spoolAsDict["lastUse"] = StringUtils.formatDateTime(spoolModel.lastUse)
	spoolAsDict["purchasedOn"] = StringUtils.formatDateTime(spoolModel.purchasedOn)

	spoolAsDict["created"] = StringUtils.formatDateTime(spoolModel.created)


	totalWeight = spoolModel.totalWeight
	usedWeight = spoolModel.usedWeight
	remainingWeight = calculateRemainingWeight(usedWeight, totalWeight)
	remainingPercentage = _calculateUsedPercentage(remainingWeight, totalWeight)
	usedPercentage = _calculateUsedPercentage(usedWeight, totalWeight)

	spoolAsDict["remainingWeight"] = StringUtils.formatFloat(remainingWeight)
	spoolAsDict["remainingPercentage"] = StringUtils.formatFloat(remainingPercentage)
	spoolAsDict["usedPercentage"] = StringUtils.formatFloat(usedPercentage)


	# Decimal and date time needs to be converted. ATTENTION orgiginal fields will be modified
	spoolAsDict["totalWeight"] = StringUtils.formatFloat(spoolModel.totalWeight)
	spoolAsDict["usedWeight"] = StringUtils.formatFloat(spoolModel.usedWeight)


	# spoolAsDict["temperature"] = StringUtils.formatSave("{:.02f}", spoolAsDict["temperature"], "")
	# spoolAsDict["weight"] = StringUtils.formatSave("{:.02f}", spoolAsDict["weight"], "")
	# spoolAsDict["remainingWeight"] = StringUtils.formatSave("{:.02f}", spoolAsDict["remainingWeight"], "")
	# spoolAsDict["usedLength"] = StringUtils.formatSave("{:.02f}", spoolAsDict["usedLength"], "")
	# spoolAsDict["usedLength"] = StringUtils.formatSave("{:.02f}", spoolAsDict["usedLength"], "")


	return spoolAsDict


def transformAllSpoolModelsToDict(allSpoolModels):
	result = []
	for job in allSpoolModels:
		spoolAsDict = transformSpoolModelToDict(job)
		result.append(spoolAsDict)
	return result
