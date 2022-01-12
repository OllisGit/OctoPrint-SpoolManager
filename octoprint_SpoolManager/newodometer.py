
# coding=utf-8
from __future__ import absolute_import

import math
# import logging
# copied from gcodeinterpreter.py Version OP 1.5.2
class NewFilamentOdometer(object):

	def __init__(self, extrusionChangedListener=None):
		# self._logger = logging.getLogger(__name__)
		self.extrusionChangedListener = extrusionChangedListener
		self.max_extruders = 10
		self.g90_extruder = False
		self.reset()

	def set_g90_extruder(self, flag=False):
		self.g90_extruder = flag

	def reset(self):
		self.currentE = [0.0]
		self.totalExtrusion = [0.0]
		self.maxExtrusion = [0.0]
		self.currentExtruder = 0    # Tool Id
		self.relativeE = False
		self.relativeMode = False
		self.duplicationMode = False
		self._fireExtrusionChangedEvent()


	# reset only the extruded ammount, the other values like relative/absolute mode must be untouched
	def reset_extruded_length(self):
		for toolIndex in range(len(self.maxExtrusion)):
			self.maxExtrusion[toolIndex] = 0.0
			self.totalExtrusion[toolIndex] = 0.0
		# yes, it it changed, but the UI should present last used value self._fireExtrusionChangedEvent()

	def processGCodeLine(self, line):

		# origLine = line
		# comment should not be during "hook-processing"
		if ";" in line:
			# comment = line[line.find(";") + 1:].strip()
			line = line[0: line.find(";")]
			pass

		if (len(line) == 0):
			return
		G = self._getCodeInt(line, "G")
		M = self._getCodeInt(line, "M")
		T = self._getCodeInt(line, "T")

		if G is not None:
			if G == 0 or G == 1:  # Move
				x = self._getCodeFloat(line, "X")
				y = self._getCodeFloat(line, "Y")
				z = self._getCodeFloat(line, "Z")
				e = self._getCodeFloat(line, "E")
				f = self._getCodeFloat(line, "F")

				if x is not None or y is not None or z is not None:
					# this is a move
					move = True
				else:
					# print head stays on position
					move = False

				if e is not None:
					if self.relativeMode or self.relativeE:
						# e is already relative, nothing to do
						pass
					else:
						e -= self.currentE[self.currentExtruder]

					# # If move with extrusion, calculate new min/max coordinates of model
					# if e > 0.0 and move:
					#     # extrusion and move -> oldPos & pos relevant for print area & dimensions
					#     self._minMax.record(oldPos)
					#     self._minMax.record(pos)

					self.totalExtrusion[self.currentExtruder] += e
					self.currentE[self.currentExtruder] += e
					self.maxExtrusion[self.currentExtruder] = max(
						self.maxExtrusion[self.currentExtruder], self.totalExtrusion[self.currentExtruder]
					)

					if self.currentExtruder == 0 and len(self.currentE) > 1 and self.duplicationMode:
						# Copy first extruder length to other extruders
						for i in range(1, len(self.currentE)):
							self.totalExtrusion[i] += e
							self.currentE[i] += e
							self.maxExtrusion[i] = max(self.maxExtrusion[i], self.totalExtrusion[i])
					self._fireExtrusionChangedEvent()
				else:
					e = 0.0

			elif G == 90:  # Absolute position
				self.relativeMode = False
				if self.g90_extruder:
					self.relativeE = False

			elif G == 91:  # Relative position
				self.relativeMode = True
				if self.g90_extruder:
					self.relativeE = True

			elif G == 92:
				x = self._getCodeFloat(line, "X")
				y = self._getCodeFloat(line, "Y")
				z = self._getCodeFloat(line, "Z")
				e = self._getCodeFloat(line, "E")

				if e is None and x is None and y is None and z is None:
					# no parameters, set all axis to 0
					self.currentE[self.currentExtruder] = 0.0
					# pos.x = 0.0
					# pos.y = 0.0
					# pos.z = 0.0
				else:
					# some parameters set, only set provided axes
					if e is not None:
						self.currentE[self.currentExtruder] = e
					# if x is not None:
					#     pos.x = x
					# if y is not None:
					#     pos.y = y
					# if z is not None:
					#     pos.z = z

		elif M is not None:
			if M == 82:  # Absolute E
				self.relativeE = False
			elif M == 83:  # Relative E
				self.relativeE = True
			# elif M == 207 or M == 208:  # Firmware retract settings
			#     s = self._getCodeFloat(line, "S")
			#     f = self._getCodeFloat(line, "F")
			#     if s is not None and f is not None:
			#         if M == 207:
			#             fwretractTime = s / f
			#             fwretractDist = s
			#         else:
			#             fwrecoverTime = (fwretractDist + s) / f
			elif M == 605:  # Duplication/Mirroring mode
				s = self._getCodeInt(line, "S")
				if s in [2, 4, 5, 6]:
					# Duplication / Mirroring mode selected. Printer firmware copies extrusion commands
					# from first extruder to all other extruders
					self.duplicationMode = True
				else:
					self.duplicationMode = False

		elif T is not None:
			if T > self.max_extruders:
				# self._logger.warning(
				#     "GCODE tried to select tool %d, that looks wrong, ignoring for GCODE analysis"
				#     % T
				# )
				print("GCODE tried to select tool %d, that looks wrong, ignoring for GCODE analysis" % T)
				pass
			elif T == self.currentExtruder:
				pass
			else:
				# pos.x -= (
				#     offsets[currentExtruder][0]
				#     if currentExtruder < len(offsets)
				#     else 0
				# )
				# pos.y -= (
				#     offsets[currentExtruder][1]
				#     if currentExtruder < len(offsets)
				#     else 0
				# )

				self.currentExtruder = T

				# pos.x += (
				#     offsets[currentExtruder][0]
				#     if currentExtruder < len(offsets)
				#     else 0
				# )
				# pos.y += (
				#     offsets[currentExtruder][1]
				#     if currentExtruder < len(offsets)
				#     else 0
				# )

				if len(self.currentE) <= self.currentExtruder:
					for _ in range(len(self.currentE), self.currentExtruder + 1):
						self.currentE.append(0.0)
				if len(self.maxExtrusion) <= self.currentExtruder:
					for _ in range(len(self.maxExtrusion), self.currentExtruder + 1):
						self.maxExtrusion.append(0.0)
				if len(self.totalExtrusion) <= self.currentExtruder:
					for _ in range(len(self.totalExtrusion), self.currentExtruder + 1):
						self.totalExtrusion.append(0.0)

	def getCurrentTool(self):
		return self.currentExtruder

	def getExtrusionAmount(self):
		return self.maxExtrusion

	def _fireExtrusionChangedEvent(self):
		if (self.extrusionChangedListener != None):
			self.extrusionChangedListener(self.getExtrusionAmount())

	def _getCodeInt(self, line, code):
		return self._getCode(line, code, int)

	def _getCodeFloat(self, line, code):
		return self._getCode(line, code, float)

	def _getCode(self, line, code, c):
		n = line.find(code) + 1
		if n < 1:
			return None
		m = line.find(" ", n)
		try:
			if m < 0:
				result = c(line[n:])
			else:
				result = c(line[n:m])
		except ValueError:
			return None

		if math.isnan(result) or math.isinf(result):
			return None

		return result

