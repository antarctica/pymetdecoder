################################################################################
# pymetdecoder/synop/section1.py
#
# Decoder routines for section 1 of a SYNOP message
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
class PrecipitationIndicator(pymetdecoder.Observation):
    """
    Precipitation indicator

    * iR(ixhVV) - Precipitation indicator
    """
    def __init__(self, raw):
        pymetdecoder.Observation.__init__(self, raw)
    def setValue(self):
        # Check indicator is valid
        if not re.match("[01234/]$", self.raw):
            raise pymetdecoder.DecodeError("{} is an invalid value for the precipitation indicator (iR)".format(self.raw))

        self.value = int(self.raw)
        self.inGroup1 = True if self.raw in [0, 1] else False
        self.inGroup3 = True if self.raw in [0, 2] else False
class WeatherIndicator(pymetdecoder.Observation):
    """
    Weather indicator

    * (iR)ix(hVV) - Weather indicator
    """
    def __init__(self, raw):
        pymetdecoder.Observation.__init__(self, raw)
    def setValue(self):
        # Check indicator is valid
        if not re.match("[1234567/]$", self.raw):
            raise pymetdecoder.DecodeError("{} is an invalid value for the weather indicator (iX)".format(self.raw))

        self.value = int(self.raw)
        self.automatic = True if self.value >= 4 else False
class LowestCloudBase(pymetdecoder.Observation):
    """
    Weather indicator

    * (iRix)h(VV) - Height above surface of the base of the lowest cloud
    """
    def __init__(self, raw, unit):
        pymetdecoder.Observation.__init__(self, raw, unit)
    def setValue(self):
        min, max = ct.codeTable1600(int(self.raw))
        self.min = min
        self.max = max
class Visibility(pymetdecoder.Observation):
    """
    Weather indicator

    * (iRixh)VV - Horizontal visibility at surface
    """
    def __init__(self, raw, unit):
        pymetdecoder.Observation.__init__(self, raw, unit)
    def setValue(self):
        visibility, quantifier = ct.codeTable4377(int(self.raw))
        if visibility is not None:
            self.visibility = visibility
        if quantifier is not None:
            self.quantifier = quantifier
class CloudCover(pymetdecoder.Observation):
    """
    Cloud cover

    * N(ddff) - Total cloud cover
    """
    def __init__(self, raw, unit):
        pymetdecoder.Observation.__init__(self, raw, unit)
    def setValue(self):
        self.value = int(self.raw)
        if self.value == 9:
            self.obscured = True
class SurfaceWind(pymetdecoder.Observation):
        """
        Surface wind

        * (N)ddff - Surface wind direction and speed
        """
        def __init__(self, raw):
            pymetdecoder.Observation.__init__(self, raw, availability=False)
        def setValue(self):
            dd = self.raw[0:2]
            ff = self.raw[2:4]

            # Set the wind direction
            self.direction = pymetdecoder.Observation(dd, value="", unit="deg")
            if self.direction.available:
                direction, calm, varAllUnknown = ct.codeTable0877(int(dd))
                self.direction.value = direction
                self.direction.calm = calm
                self.direction.varAllUnknown = varAllUnknown

            # Set the wind speed
            self.speed = pymetdecoder.Observation(ff, value="")
            if self.speed.available:
                self.speed.value = int(ff)

            # Tidy attributes
            delattr(self, "raw")
class Temperature(pymetdecoder.Observation):
    """
    Temperature observation

    * 1sTTT - air temperature
    * 2sTTT - dewpoint temperature
    """
    def __init__(self, raw, unit):
        pymetdecoder.Observation.__init__(self, raw, unit)
    def setValue(self):
        # Get the sign (sn) and the temperature (TTT)
        sn  = self.raw[1:2]
        TTT = self.raw[2:5]

        # Set availability
        if not self.isAvailable(value=sn) or not self.isAvailable(value=TTT):
            self.available = False

        # Set the values
        if self.available:
            if TTT[2] == "/":
                TTT = TTT[0:2] + "0"
            sn = int(sn)
            TTT = int(TTT)
            if sn not in [0,1]:
                raise pymetdecoder.DecodeError("{} is not a valid temperature sign code for code table 3845".format(sn))

            # Set the value
            self.value = (TTT / 10.0) * (1 if sn == 0 else -1)
class RelativeHumidity(pymetdecoder.Observation):
    """
    Relative humidity

    * 29UUU - relative humidity
    """
    def __init__(self, raw, unit):
        pymetdecoder.Observation.__init__(self, raw, unit)
    def setValue(self):
        # Get the relative humidity
        UUU = self.raw[2:5]

        # Set the values
        if self.available:
            UUU = int(UUU)
            if UUU > 100:
                raise pymetdecoder.DecodeError("{} is not a valid relative humidity".format(UUU))
            self.value = UUU
