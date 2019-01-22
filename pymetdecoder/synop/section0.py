################################################################################
# pymetdecoder/synop/section0.py
#
# Decoder routines for section 0 of a SYNOP message
#
# TDBA 2019-01-21:
#   * First version
################################################################################
# CONFIGURATION
################################################################################
import re, types, pymetdecoder
from . import code_tables as ct
################################################################################
# OBSERVATION CLASSES
################################################################################
class StationType(pymetdecoder.Observation):
    """
    Station Type

    * MMMM - station type
    """
    def __init__(self, raw):
        pymetdecoder.Observation.__init__(self, raw, availability=False)
    def setValue(self):
        # Set the value
        if re.match("^(AA|BB|OO)XX$", self.raw):
            self.value = self.raw
        else:
            raise pymetdecoder.DecodeError("{} is an invalid station type".format(self.raw))
class Callsign(pymetdecoder.Observation):
    """
    Callsign

    * D...D - Ship's callsign consisting of three or more alphanumeric characters
    * A1bwnnn - WMO regional association area
    """
    def __init__(self, raw):
        pymetdecoder.Observation.__init__(self, raw, availability=False)
    def setValue(self):
        # Set the values
        if re.match("^(1[1-7]|2[1-6]|3[1-4]|4[1-8]|5[1-6]|6[1-6]|7[1-4])\d{3}$", self.raw):
            self.region = ct.codeTable0161(self.raw[0:2])
            self.id = self.raw
        elif re.match("^[A-Z\d]{3,}", self.raw):
            self.id = self.raw
        else:
            raise pymetdecoder.DecodeError("Unable to determine {} callsign information from {}".format(self.data["stationType"].value, self.raw))
class ObservationTime(pymetdecoder.Observation):
    """
    Observation time

    * YYGG - day and hour of observation
    """
    def __init__(self, raw):
        pymetdecoder.Observation.__init__(self, raw, availability=False)
    def setValue(self):
        # Get the values
        YY = self.raw[0:2]
        GG = self.raw[2:4]

        # Check observation time values are valid
        if int(YY) > 31:
            raise pymetdecoder.DecodeError("{} is an invalid value for observation day (YY)".format(YY))
        if int(GG) > 24:
            raise pymetdecoder.DecodeError("{} is an invalid value for observation hour (GG)".format(GG))

        # Set the values
        self.day  = YY
        self.hour = GG
class WindIndicator(pymetdecoder.Observation):
    """
    Wind indicator

    * iw - Indicator for source and units of wind speed
    """
    def __init__(self, raw):
        pymetdecoder.Observation.__init__(self, raw)
    def setValue(self):
        # Check indicator is valid
        if not re.match("[0134/]$", self.raw):
            raise pymetdecoder.DecodeError("{} is an invalid value for the wind indicator (iw)".format(self.raw))

        # Set the values
        self.value = int(self.raw)
        self.unit  = "m/s" if self.value < 2 else "KT"
        self.estimated = True if self.value in [0, 3] else False
class StationPosition(pymetdecoder.Observation):
    """
    Station position

    * 99LaLaLa QcLoLoLoLo - Latitude, globe quadrant and longitude
    * MMMULaULo h0h0h0h0im - Mobile land station position
    """
    def __init__(self, raw):
        pymetdecoder.Observation.__init__(self, raw)
    def setValue(self):
        # Check we have a valid number of raw groups
        if len(self.raw.split()) not in [2, 4]:
            raise pymetdecoder.DecodeError("Invalid groups for decoding station position ({})".format(self.raw))

        # Set the values
        LaLaLa   = int(self.raw[2:5]) # latitude
        Qc       = int(self.raw[6:7]) # quadrant
        LoLoLoLo = int(self.raw[7:11]) # longitude
        self.latitude  = "{:.1f}".format(LaLaLa / (-10.0 if Qc in [3, 5] else 10.0))
        self.longitude = "{:.1f}".format(LoLoLoLo / (-10.0 if Qc in [5, 7] else 10.0))

        # The following is only for OOXX stations (MMMULaULo h0h0h0h0im)
        if len(self.raw.split()) == 4:
            MMM      = int(self.raw[12:15]) # Marsden square
            ULa      = int(self.raw[15:16]) # Latitude unit
            ULo      = int(self.raw[16:17]) # Longitude unit
            h0h0h0h0 = int(self.raw[18:22]) # Elevation
            im       = int(self.raw[22:23]) # Elevation indicator/confidence
            if (not 1 <= MMM <= 623) and (not 901 <= MMM <= 936):
                raise pymetdecoder.DecodeError("{} is not a valid Marsden Square".format(MMM))

            confidence = ["Poor", "Excellent", "Good", "Fair"]
            self.marsdenSquare = MMM
            self.elevation = h0h0h0h0
            self.elevationUnits = "m" if im <= 4 else "ft"
            self.confidence = confidence[im % 4]
    def isAvailable(self, char="/", value=None):
        return False if re.match("^99/// /////", self.raw) else True
