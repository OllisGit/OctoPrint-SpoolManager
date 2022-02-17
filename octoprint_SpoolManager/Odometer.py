# coding=utf-8
# borrowed from FilamentManager
# master commit hash: bd1a9c0 on 1 Dec 2017
from __future__ import absolute_import

__author__ = "Sven Lohrmann <malnvenshorn@gmail.com> based on work by Gina Häußge <osd@foosel.net>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2017 Sven Lohrmann - Released under terms of the AGPLv3 License"

import re

########## DEPRECATED use newodometer

class FilamentOdometer(object):
	regexE = re.compile(r'.*E(-?\d+(\.\d+)?)')
	regexT = re.compile(r'^T(\d+)')

	class ToolExtrusion:
		lastExtrusion = 0.0
		totalExtrusion = 0.0
		maxExtrusion = 0.0
		myValue = 0.0

	def __init__(self):
		self.g90_extruder = True
		self.reset()

	def reset(self):
		self.relativeMode = False
		self.relativeExtrusion = False
		self.currentToolName = "Tool0"
		self.allToolExtrusions = {self.currentToolName : self.ToolExtrusion()} # Tool0 must always be there, default extruder
		# self.lastExtrusion = [0.0]
		# self.totalExtrusion = [0.0]
		# self.maxExtrusion = [0.0]


	def reset_extruded_length(self):
		# tools = len(self.maxExtrusion)
		# self.maxExtrusion = [0.0] * tools
		# self.totalExtrusion = [0.0] * tools
		for toolName in self.allToolExtrusions:
			self.allToolExtrusions[toolName].totalExtrusion = 0.0
			self.allToolExtrusions[toolName].maxExtrusion = 0.0
			self.allToolExtrusions[toolName].myValue = 0.0

	def parse(self, gcode, cmd):
		if gcode is None:
			return

		if gcode == "G1" or gcode == "G0":  # move
			e = self._get_float(cmd, self.regexE)
			if e is not None:
				if (e > 0.0):
					self._getCurrentToolExtrusion().myValue += e

				if self.relativeMode or self.relativeExtrusion:
					# e is already relative, nothing to do
					pass
				else:
					# e -= self.lastExtrusion[self.currentTool]
					e -= self._getCurrentToolExtrusion().lastExtrusion
				# self.totalExtrusion[self.currentTool] += e
				# self.lastExtrusion[self.currentTool] += e
				# self.maxExtrusion[self.currentTool] = max(self.maxExtrusion[self.currentTool],
				# 										  self.totalExtrusion[self.currentTool])
				self._getCurrentToolExtrusion().totalExtrusion += e
				self._getCurrentToolExtrusion().lastExtrusion += e
				self._getCurrentToolExtrusion().maxExtrusion = max(self._getCurrentToolExtrusion().maxExtrusion,
																   self._getCurrentToolExtrusion().totalExtrusion)


		elif gcode == "G90":  # set to absolute positioning
			self.relativeMode = False
			if self.g90_extruder:
				self.relativeExtrusion = False
		elif gcode == "G91":  # set to relative positioning
			self.relativeMode = True
			if self.g90_extruder:
				self.relativeExtrusion = True
		elif gcode == "G92":  # set position
			e = self._get_float(cmd, self.regexE)
			if e is not None:
				# self.lastExtrusion[self.currentTool] = e
				self._getCurrentToolExtrusion().lastExtrusion = e
		elif gcode == "M82":  # set extruder to absolute mode
			self.relativeExtrusion = False
		elif gcode == "M83":  # set extruder to relative mode
			self.relativeExtrusion = True
		elif gcode.startswith("T"):  # select tool
			toolIndex = self._get_int(cmd, self.regexT)
			if toolIndex is not None:
				self.currentToolName = "Tool" + str(toolIndex)
				if ( (self.currentToolName in self.allToolExtrusions) == False):
					self.allToolExtrusions[self.currentToolName] = self.ToolExtrusion()
					# if len(self.lastExtrusion) <= self.currentTool:
					# 	for i in xrange(len(self.lastExtrusion), self.currentTool + 1):
					# 		self.lastExtrusion.append(0.0)
					# 		self.totalExtrusion.append(0.0)
					# 		self.maxExtrusion.append(0.0)

	def set_g90_extruder(self, flag=True):
		self.g90_extruder = flag

	def get_extrusion(self, toolName):
		# return self.maxExtrusion
		return self.allToolExtrusions[toolName].maxExtrusion

	def getExtrusionForAllTools(self):
		result = 0.0
		for toolName in self.allToolExtrusions:
			result += self.allToolExtrusions[toolName].maxExtrusion
		return result

	def get_current_tool(self):
		return self.currentToolName

	def _getCurrentToolExtrusion(self):
		return self.allToolExtrusions[self.currentToolName]

	def _get_int(self, cmd, regex):
		result = regex.match(cmd)
		if result is not None:
			return int(result.group(1))
		else:
			return None

	def _get_float(self, cmd, regex):
		result = regex.match(cmd)
		if result is not None:
			return float(result.group(1))
		else:
			return None
