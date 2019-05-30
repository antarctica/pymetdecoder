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
import re, types, pymetdecoder, logging
from . import code_tables as ct
################################################################################
# OBSERVATION CLASSES
################################################################################
class PrecipitationIndicator(pymetdecoder.Observation):
    """
    Precipitation indicator

    * iR(ixhVV) - Precipitation indicator
    """
    def setValue(self):
        # Check indicator is valid
        if not re.match("[01234/]$", self.raw):
            logging.warning("{} is an invalid value for the precipitation indicator (iR)".format(self.raw))
            self.available = False
            return

        self.value = int(self.raw)
        self.inGroup1 = True if self.raw in [0, 1] else False
        self.inGroup3 = True if self.raw in [0, 2] else False
class WeatherIndicator(pymetdecoder.Observation):
    """
    Weather indicator

    * (iR)ix(hVV) - Weather indicator
    """
    def setValue(self):
        # Check indicator is valid
        if not re.match("[1234567/]$", self.raw):
            logging.warning("{} is an invalid value for the weather indicator (iX)".format(self.raw))
            self.available = False
            return

        self.value = int(self.raw)
        self.automatic = True if self.value >= 4 else False
class LowestCloudBase(pymetdecoder.Observation):
    """
    Weather indicator

    * (iRix)h(VV) - Height above surface of the base of the lowest cloud
    """
    def setValue(self):
        min, max, quantifier = ct.codeTable1600(int(self.raw))
        self.min = min
        self.max = max
        self.quantifier = quantifier
class Visibility(pymetdecoder.Observation):
    """
    Weather indicator

    * (iRixh)VV - Horizontal visibility at surface
    """
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
    def setValue(self):
        self.value = int(self.raw)
        if self.value == 9:
            self.obscured = True
class SurfaceWind(pymetdecoder.Observation):
        """
        Surface wind

        * (N)ddff - Surface wind direction and speed
        """
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
class Temperature(pymetdecoder.Observation):
    """
    Temperature observation

    * 1sTTT - air temperature
    * 2sTTT - dewpoint temperature
    """
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
    def setValue(self):
        # Get the relative humidity
        UUU = self.raw[2:5]

        # Set the values
        if self.available:
            UUU = int(UUU)
            if UUU > 100:
                raise pymetdecoder.DecodeError("{} is not a valid relative humidity".format(UUU))
            self.value = UUU
class Pressure(pymetdecoder.Observation):
    """
    Pressure

    * 3P0P0P0P0 - Station level pressure
    * 4PPPP - Sea level pressure
    """
    def setValue(self):
        # Set availability
        PPPP = self.raw[1:5]
        if not self.isAvailable(value=PPPP):
            self.available = False

        # Set the value
        if self.available:
            PPPP = int(PPPP)
            self.value = (PPPP / 10) + (0 if PPPP > 500 else 1000)
class Geopotential(pymetdecoder.Observation):
    """
    Geopotential

    * 4ahhh - Geopotential level and height
    """
    def setValue(self):
        # Get the surface data
        a = self.raw[1]
        self.surface = pymetdecoder.Observation(a, value="", unit="hPa")
        if self.surface.available:
            self.surface.value = ct.codeTable0264(int(a))

        # Get the height data
        hhh = self.raw[2:5]
        self.height = pymetdecoder.Observation(hhh, value="", unit="gpm")
        if self.height.available:
            a = int(a)
            hhh = int(hhh)
            if a == 2:
                hhh += 1000 if hhh < 300 else 0
            elif a == 7:
                hhh += 3000 if hhh < 500 else 2000
            elif a == 8:
                hhh += 1000
            self.height.value = hhh

        # Tidy attributes
        delattr(self, "raw")
class PressureTendency(pymetdecoder.Observation):
    """
    Pressure tendency

    * 5appp - Pressure tendency over the past three hours
    """
    def setValue(self):
        # Set availability
        if not self.isAvailable(value=self.raw[1:5]):
            self.available = False

        # Set the value
        if self.available:
            a   = self.raw[1:2]
            ppp = self.raw[2:5]
            if not self.isAvailable(value=a) or not self.isAvailable(value=ppp):
                self.available = False
            else:
                # Check indicator is valid
                if not re.match("[012345678/]$", a):
                    logging.warning("{} is an invalid value for the precipitation indicator (a)".format(a))
                    self.available = False
                    return
                self.tendency = a if a == "/" else int(a)
                self.change   = float("{:.1f}".format(int(ppp) / (10.0 if self.tendency < 5 else -10.0)))
class Precipitation(pymetdecoder.Observation):
    """
    Precipitation

    * 6RRRt - Precipitation amount
    """
    def setValue(self):
        # Get the precipitation data
        RRR = self.raw[1:4]
        self.amount = pymetdecoder.Observation(RRR, value="", unit="mm")
        if self.amount.available:
            value, quantifier, trace = ct.codeTable3590(int(RRR))
            self.amount.value = value
            self.amount.quantifier = quantifier
            self.amount.trace = trace

        # Get the time before obs
        t = self.raw[4:5]
        self.timeBeforeObs = pymetdecoder.Observation(t, value="", unit="h")
        if self.timeBeforeObs.available:
            if int(t) == 0:
                self.timeBeforeObs.available = False
            else:
                self.timeBeforeObs.value = ct.codeTable4019(int(t))

        # Tidy attributes
        delattr(self, "available")
class Weather(pymetdecoder.Observation):
    """
    Weather

    * 7wwWW - Present and past weather
    """
    def setValue(self):
        if self.available:
            self.value = int(self.raw)
class CloudTypes(pymetdecoder.Observation):
    """
    Cloud Types/Amount

    * 8Nhhh - Cloud types and base of lowest cloud
    """
    def setValue(self):
        # Set availability
        if not self.isAvailable(value=self.raw[1:5]):
            self.available = False

        # Get the components
        Nh = self.raw[1:2] # Amount of lowest cloud if there is lowest cloud, else base of middle cloud
        CL = self.raw[2:3] # Lowest cloud type
        CM = self.raw[3:4] # Middle cloud type
        CH = self.raw[4:5] # High cloud type

        # Check if sky obscured or observation not made
        self.obscured = True if Nh == 9 else False

        # Get the cloud types
        self.lowCloudType    = self._setCloudValue(CL)
        self.middleCloudType = self._setCloudValue(CM)
        self.highCloudType   = self._setCloudValue(CH)

        # Add the oktas
        if Nh != "0" and Nh != "/":
            if self.lowCloudType.available and 1 <= self.lowCloudType.value <= 9:
                self.lowCloudCover = pymetdecoder.Observation(Nh, value=int(Nh))
            elif self.middleCloudType.available and 1 <= self.middleCloudType.value <= 9:
                self.middleCloudCover = pymetdecoder.Observation(Nh, value=int(Nh))
            else:
                logging.warning("Cloud cover (Nh = {}) reported, but there are no low or middle clouds (CL = {}, CM = {})".format(Nh, CL, CM))
    def _setCloudValue(self, val):
        try:
            obs = pymetdecoder.Observation(val, value=int(val))
        except:
            obs = pymetdecoder.Observation(val, value=val)
        return obs
class ExactObservationTime(pymetdecoder.Observation):
    """
    Exact observation time

    * 9GGgg - Time of observation in hours and minutes and UTC
    """
    def setValue(self):
        # Set availability
        if not self.isAvailable(value=self.raw[1:5]):
            self.available = False

        # Get the components
        GG = self.raw[1:3]
        gg = self.raw[3:5]

        # Check if values are valid
        if self.available:
            if int(GG) > 24:
                raise pymetdecoder.DecodeError("Exact observation hour is out of range (GG = {})".format(GG))
            if int(gg) > 60:
                raise pymetdecoder.DecodeError("Exact observation minute is out of range (gg = {})".format(gg))

        # Set values
        self.hour   = int(GG)
        self.minute = int(gg)
