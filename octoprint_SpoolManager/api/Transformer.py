# coding=utf-8
from __future__ import absolute_import

from octoprint_SpoolManager.models.SpoolModel import SpoolModel
from octoprint_SpoolManager.common import StringUtils

def transformSpoolModelToDict(spoolModel):
	spoolAsDict = spoolModel.__data__

	# Date time needs to be converted
	spoolAsDict["firstUse"] = StringUtils.formatDateTime(spoolModel.firstUse)
	spoolAsDict["lastUse"] = StringUtils.formatDateTime(spoolModel.lastUse)
	spoolAsDict["purchasedOn"] = StringUtils.formatDateTime(spoolModel.purchasedOn)

	spoolAsDict["created"] = StringUtils.formatDateTime(spoolModel.created)

	# Decimal and date time needs to be converted
	spoolAsDict["totalWeight"] = StringUtils.formatFloat(spoolModel.totalWeight)
	spoolAsDict["usedWeight"] = StringUtils.formatFloat(spoolModel.usedWeight)

	# spoolAsDict["temperature"] = StringUtils.formatSave("{:.02f}", spoolAsDict["temperature"], "")
	# spoolAsDict["weight"] = StringUtils.formatSave("{:.02f}", spoolAsDict["weight"], "")
	# spoolAsDict["remainingWeight"] = StringUtils.formatSave("{:.02f}", spoolAsDict["remainingWeight"], "")
	# spoolAsDict["usedLength"] = StringUtils.formatSave("{:.02f}", spoolAsDict["usedLength"], "")
	# spoolAsDict["usedLength"] = StringUtils.formatSave("{:.02f}", spoolAsDict["usedLength"], "")

	# spoolAsDict["firstUse"] = spoolModel.firstUse.strftime('%d.%m.%Y %H:%M')
	# spoolAsDict["lastUse"] = spoolModel.lastUse.strftime('%d.%m.%Y %H:%M')

	# spoolAsDict["firstUse"] = self._formatDateOrNone( spoolModel.firstUse )
	# spoolAsDict["lastUse"] = self._formatDateOrNone( spoolModel.lastUse )

	return spoolAsDict


def transformAllSpoolModelsToDict(allSpoolModels):
	result = []
	for job in allSpoolModels:
		spoolAsDict = transformSpoolModelToDict(job)
		result.append(spoolAsDict)
	return result
