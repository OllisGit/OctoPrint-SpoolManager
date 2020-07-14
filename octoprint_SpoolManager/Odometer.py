# coding=utf-8
# master commit hash: bd1a9c0 on 1 Dec 2017
from __future__ import absolute_import

__author__ = "Sven Lohrmann <malnvenshorn@gmail.com> based on work by Gina Häußge <osd@foosel.net>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2017 Sven Lohrmann - Released under terms of the AGPLv3 License"

import re


class FilamentOdometer(object):

    regexE = re.compile(r'.*E(-?\d+(\.\d+)?)')
    regexT = re.compile(r'^T(\d+)')

    def __init__(self):
        self.g90_extruder = True
        self.reset()

    def reset(self):
        self.relativeMode = False
        self.relativeExtrusion = False
        self.lastExtrusion = [0.0]
        self.totalExtrusion = [0.0]
        self.maxExtrusion = [0.0]
        self.currentTool = 0

    def reset_extruded_length(self):
        tools = len(self.maxExtrusion)
        self.maxExtrusion = [0.0] * tools
        self.totalExtrusion = [0.0] * tools

    def parse(self, gcode, cmd):
        if gcode is None:
            return

        if gcode == "G1" or gcode == "G0":  # move
            e = self._get_float(cmd, self.regexE)
            if e is not None:
                if self.relativeMode or self.relativeExtrusion:
                    # e is already relative, nothing to do
                    pass
                else:
                    e -= self.lastExtrusion[self.currentTool]
                self.totalExtrusion[self.currentTool] += e
                self.lastExtrusion[self.currentTool] += e
                self.maxExtrusion[self.currentTool] = max(self.maxExtrusion[self.currentTool],
                                                          self.totalExtrusion[self.currentTool])
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
                self.lastExtrusion[self.currentTool] = e
        elif gcode == "M82":  # set extruder to absolute mode
            self.relativeExtrusion = False
        elif gcode == "M83":  # set extruder to relative mode
            self.relativeExtrusion = True
        elif gcode.startswith("T"):  # select tool
            t = self._get_int(cmd, self.regexT)
            if t is not None:
                self.currentTool = t
                if len(self.lastExtrusion) <= self.currentTool:
                    for i in xrange(len(self.lastExtrusion), self.currentTool + 1):
                        self.lastExtrusion.append(0.0)
                        self.totalExtrusion.append(0.0)
                        self.maxExtrusion.append(0.0)

    def set_g90_extruder(self, flag=True):
        self.g90_extruder = flag

    def get_extrusion(self):
        return self.maxExtrusion

    def get_current_tool(self):
        return self.currentTool

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
