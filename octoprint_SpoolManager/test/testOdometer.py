import logging
import unittest

from octoprint_SpoolManager import NewFilamentOdometer
from octoprint_SpoolManager.Odometer import FilamentOdometer


class TestOdometer(unittest.TestCase):

    def test_loadJobSettings(self):

        logging.basicConfig(level=logging.DEBUG)
        testLogger = logging.getLogger("testLogger")
        logging.info("Start Odometer-Test")

        self.filamentOdometer = FilamentOdometer()
        self.myFilamentOdometer = NewFilamentOdometer()
        # filename = "/Users/o0632/0_Projekte/3DDruck/OctoPrint/OctoPrint-FilamentManager/issues/issue24/Ornaments.01_colored.gcode"
        filename = "/Users/o0632/0_Projekte/3DDruck/OctoPrint/GitHub-Issues/FilamentManager/issue24/LeftAnchorBlock_0.2mm_ABS_MK3SMMU2S_12h19m.gcode"
        # filename = "/Users/o0632/0_Projekte/3DDruck/OctoPrint/OctoPrint-FilamentManager/issues/issue27/logs+gcode/root-miniatures-cat.stl-809000d_0.2mm_PLA+PVA_MK3SMMU2S_6h13m.gcode"
        # M204 P1250 R1250 T1250 ; sets acceleration (P, T) and retract acceleration (R), mm/sec^2
        lineCounter = 0
        with open(filename) as fp:
            for line in fp:
                lineCounter = lineCounter +1
                stripedLine = line.strip();
                # print(stripedLine)
                gcode = None

                if (stripedLine.startswith("G1")):
                    gcode = "G1"
                if (stripedLine.startswith("G0")):
                    gcode = "G0"
                if (stripedLine.startswith("G90")):
                    gcode = "G90"
                if (stripedLine.startswith("G91")):
                    gcode = "G91"
                if (stripedLine.startswith("G92")):
                    gcode = "G92"
                if (stripedLine.startswith("M82")):
                    gcode = "M82"
                if (stripedLine.startswith("M83")):
                    gcode = "M83"
                if (stripedLine.startswith("T")):
                    gcode = stripedLine.split()[0]


                if (lineCounter == 358):
                    # break
                    pass
                self.filamentOdometer.parse(gcode, stripedLine)
                self.myFilamentOdometer.processGCodeLine(stripedLine)

                # print(str(lineCounter) + " " + str(self.filamentOdometer.get_extrusion()) + " " + str(self.myFilamentOdometer.getExtrusionAmount()))
                # if (lineCounter == 1000):
                #     break

        extrusion = self.filamentOdometer.allToolExtrusions
        myExtrusion = self.myFilamentOdometer.getExtrusionAmount()

        print(filename)
        print("Old-Implementation")
        for total in extrusion:
			print(total + " " + str(extrusion[total].totalExtrusion))
        print("New-Implementation")
        print(myExtrusion)

if __name__ == '__main__':
	print("Start Odometer Test")
	unittest.main()
	print("Finished")
