################################################################################
# pymetdecoder/synop/__init__.py
#
# SYNOP decoder module for pymetdecoder
#
# TDBA 2019-01-16:
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

    Section 0:
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

    Section 0:
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

    Section 0:
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

    Section 0:
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

    Section 0:
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
class PrecipitationIndicator(pymetdecoder.Observation):
    """
    Precipitation indicator

    Section 1:
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

    Section 1:
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

    Section 1:
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

    Section 1:
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

    Section 1:
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

        Section 1:
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
# class Temperature(pymetdecoder.Observation):
#     """
#     Temperature observation
#
#     Section 1:
#         * 1sTTT - air temperature
#         * 2sTTT - dewpoint temperature
#     """
#     def __init__(self, raw, unit):
#         pymetdecoder.Observation.__init__(self, raw, unit)
#
#         # Get the sign (sn) and the temperature (TTT)
#         sn  = self.raw[1:2]
#         TTT = self.raw[2:5]
#
#         # Set availability
#         if not self.isAvailable(value=sn) or not self.isAvailable(value=TTT):
#             self.available = False
#
#         # Set the values
#         if self.available:
#             if TTT[2] == "/":
#                 TTT = temperature[TTT:2] + "0"
#             sn = int(sn)
#             TTT = int(TTT)
#             if sn not in [0,1]:
#                 raise pymetdecoder.DecodeError("{} is not a valid temperature sign code for code table 3845".format(sn))
#
#             # Set the value
#             self.value = (TTT / 10.0) * (1 if sn == 0 else -1)
################################################################################
# REPORT CLASSES
################################################################################
class SYNOP(pymetdecoder.Report):
    def __init__(self, message):
        """
        Initialises the SYNOP report object
        """
        pymetdecoder.Report.__init__(self, message)

    # Decode the SYNOP
    def decode(self):
        """
        Decodes the SYNOP
        """
        # Initialise data attribute
        self.data = {}

        # Create iterator of the message components
        groups = iter(self.message.split())

        ### SECTION 0 ###
        try:
            # Get the message type
            self.data["stationType"] = StationType(next(groups))

            # Add callsign for non-AAXX stations
            if self.data["stationType"].value != "AAXX":
                self.data["callsign"] = Callsign(next(groups))

            # Get date, time and wind indictator
            self.parseYYGGi(next(groups))

            # Now add the station ID if it is an AAXX station. Otherwise, add the current position
            if self.data["stationType"].value == "AAXX":
                group = next(groups)
                if not _isGroupValid(group, allowSlashes=False):
                    raise pymetdecoder.DecodeError("{} is an invalid IIiii group".format(group))
                self.data["stationID"] = pymetdecoder.Observation(group, availability=False, value=group)
            elif self.data["stationType"].value == "BBXX":
                self.data["stationPosition"] = StationPosition("{} {}".format(next(groups), next(groups)))
            else: # OOXX
                self.data["stationPosition"] = StationPosition("{} {} {} {}".format(next(groups), next(groups), next(groups), next(groups)))

            # If this section ends with NIL, that's the end of the SYNOP
            next_group = next(groups)
            if next_group == "NIL":
                return

            # ### SECTION 1 ###
            # Get precipitation indicator, weather indicator, base of lowest cloud and visibility
            self.parseiihVV(next_group)

            # Get cloud cover, wind direction and speed
            self.parseNddff(next(groups))

            # If the raw wind speed was 99 units, then we have to check if the next group is 00fff
            # as this represents wind speeds of >99 units
            next_group = next(groups)
            if hasattr(self.data["surfaceWind"], "speed") and self.data["surfaceWind"].speed.raw == "99":
                if re.match("^00\d{3}", next_group):
                    self.data["surfaceWind"].speed.value = int(next_group[2:5])
                    self.data["surfaceWind"].speed.raw += " {}".format(next_group)
                    next_group = next(groups)
            #
            # # Parse the next group, based on the group header
            # for i in range(1, 10):
            #     header = int(next_group[0:1])
            #     if header == i:
            #         if i == 1:
            #             self.parseAirTemperature(next_group)
            #         elif i == 2:
            #             self.parseDewpointHumidity(next_group)
            #         elif i == 3:
            #             self.parseStationLevelPressure(next_group)
            #         elif i == 4:
            #             self.parseSeaLevelPressureGeopotential(next_group)
            #         elif i == 5:
            #             self.parsePressureTendency(next_group)
            #         next_group = next(groups)
        except StopIteration:
            return

    # Functions to decode individual groups
    def parseYYGGi(self, group): # YYGGi
        """
        Parses the observation time and wind indicator group (YYGGi)
        """
        # Check group matches regular expression
        if not self._isGroupValid(group):
            raise pymetdecoder.DecodeError("{} is an invalid YYGGi group".format(group))

        # Add observation time to data
        self.data["obsTime"] = ObservationTime(group[0:4])

        # Add wind indicator to data
        self.data["windIndicator"] = WindIndicator(group[4])
    def parseiihVV(self, group): # iihVV
        """
        Parses the precipitation and weather indicator and cloud base group (iihVV)
        """
        # Check group matches regular expression
        if not self._isGroupValid(group):
            raise pymetdecoder.DecodeError("{} is an invalid iihVV group".format(group))

        # Get the precipitation indicator (iR)
        self.data["precipitationIndicator"] = PrecipitationIndicator(group[0:1])

        # Get the weather indicator (ix)
        self.data["weatherIndicator"] = WeatherIndicator(group[1:2])

        # Get the lowest cloud base (h)
        self.data["lowestCloudBase"] = LowestCloudBase(group[2:3], unit="m")

        # Get the horizonal visibility (VV)
        self.data["visibility"] = Visibility(group[3:5], unit="m")
    def parseNddff(self, group): # Nddff
        """
        Parses the cloud cover and surface wind group (Nddff)
        """
        if not self._isGroupValid(group):
            raise pymetdecoder.DecodeError("{} is an invalid Nddff group".format(group))

        # Get total cloud cover (N)
        self.data["cloudCover"] = CloudCover(group[0:1], unit="okta")

        # Get wind direction (dd) and wind speed (ff)
        self.data["surfaceWind"] = SurfaceWind(group[1:5])
        if hasattr(self.data["surfaceWind"], "speed") and hasattr(self.data["windIndicator"], "unit"):
            self.data["surfaceWind"].speed.setUnit(self.data["windIndicator"].unit)

    def parseAirTemperature(self, group): # 1snTTT
        """
        Parses the air temperature group (1snTTT)
        """
        if not self._isGroupValid(group):
            raise pymetdecoder.DecodeError("{} is an invalid air temperature group".format(group))

        # Prepare the data
        if "temperature" not in self.data:
            self.data["temperature"] = {}
        self.data["temperature"]["air"] = Temperature(group, "Cel")

        # self._parseTemperature(group, sn, TTT, "air")
    def parseDewpointHumidity(self, group): # 2snTTT or 29UUU
        """
        Parses the dewpoint temperature/relative humidity group (2snTTT or 29UUU)
        """
        if not self._isGroupValid(group):
            raise pymetdecoder.DecodeError("{} is an invalid dewpoint temperature/relative humidity group".format(group))

        # Get sign and temperature
        sn  = group[1:2]
        TTT = group[2:5]

        # If sn is 9, we're dealing with relative humidity.
        # Otherwise, parse the temperature
        if sn == "9":
            data = { "available": True, "raw": group }
            if TTT == "///":
                data["available"] = False
            else:
                TTT = int(TTT)
                if TTT > 100:
                    raise pymetdecoder.DecodeError("{} is not a valid relative humidity".format(TTT))
                data["unit"] = "%"
                data["value"] = TTT
            self.data["relativeHumidity"] = data
        else:
            self._parseTemperature(group, sn, TTT, "dewpoint")
    def parseStationLevelPressure(self, group): # 3P0P0P0P0
        """
        Parses the station level pressure group (3P0P0P0P0)
        """
        if not self._isGroupValid(group):
            raise pymetdecoder.DecodeError("{} is an invalid station level pressure group".format(group))

        # Create the data array
        P0P0P0P0 = group[1:5]
        data = { "available": True, "raw": group, "unit": "hPa" }
        if P0P0P0P0[1:4] == "///":
            data["available"] = False
        else:
            data["value"] = (int(P0P0P0P0) / 10) + (0 if int(P0P0P0P0) > 500 else 1000)
        self.data["stationPressure"] = data
    def parseSeaLevelPressureGeopotential(self, group): # 4PPPP or 4ahhh
        """
        Parses the sea level pressure/geopotential group (4PPPP or 4ahhh)
        """
        if not self._isGroupValid(group):
            raise pymetdecoder.DecodeError("{} is an invalid sea level pressure/geopotential group".format(group))

        # Determine if this is pressure or geopotential height
        a = group[1]
        if a in ["0", "9"]:
            self._parsePressure(group, "seaLevelPressure")
        elif a in ["1", "2", "5", "7", "8", "/"]:
            # Get the surface
            surface = { "available": True, "unit": "hPa" }
            if a == "/":
                surface["available"] = False
            else:
                surface["value"] = ct.codeTable0264(int(a))

            # Get the height
            hhh    = group[2:5]
            height = { "available": True, "unit": "gpm" }
            if hhh == "///":
                height["available"] = False
            else:
                a = int(a)
                hhh = int(hhh)
                if a == 2:
                    hhh += 1000 if hhh < 300 else 0
                elif a == 7:
                    hhh += 3000 if hhh < 500 else 2000
                elif a == 8:
                    hhh += 1000
                height["value"] = hhh
            self.data["geopotential"] = { "surface": surface, "height": height, "raw": group }
    def parsePressureTendency(self, group): # 5appp
        """
        Parses the pressure tendency group (5appp)
        """
        if not self._isGroupValid(group):
            raise pymetdecoder.DecodeError("{} is an invalid pressure tendency group".format(group))

        # Create the data array
        data = { "available": True, "raw": group, "unit": "hPa" }
        if group[1:5] == "////":
            data["available"] = False
        else:
            a, description = ct.codeTable0200(int(group[1:2]))
            ppp = group[2:5]
            if ppp == "///":
                data["available"] = False
            else:
                data["tendency"] = a
                data["change"]   = "{:.1f}".format(ppp / (10.0 if a < 5 else -10.0))
        self.data["pressureTendency"] = data
        #
        # foo = pymetdecoder.Observation("12345", "m")
        # print(foo)

    def _isGroupValid(self, group, length=5, allowSlashes=True, multipleGroups=False):
        """
        Checks if group is valid.
        In most cases, a valid group is 5 alphanumeric characters and/or slashes (/)
        """
        regexp_parts = ["\d"]
        if allowSlashes:
            regexp_parts.append("\/")
        if multipleGroups:
            regexp_parts.append(" ")
        regexp = "[{}]{{{}}}".format("".join(regexp_parts), length)
        return bool(re.match(regexp, group))
    def _parseTemperature(self, group, sign, temperature, type):
        """
        Parses a temperature group
        """
        # Prepare the data
        data = { "available": True, "raw": group }
        if sign == "/" or temperature == "///":
            data["available"] = False
        else:
            if temperature[2] == "/":
                temperature = temperature[0:2] + "0"
            sign = int(sign)
            temperature = int(temperature)
            # Check sign is valid
            if sign not in [0, 1]:
                raise pymetdecoder.DecodeError("{} is not a valid temperature sign code for code table 3845".format(sign))

            # Add data
            data["unit"]  = "Cel"
            data["value"] = (temperature / 10.0) * (1 if sign == 0 else -1)
        if "temperature" not in self.data:
            self.data["temperature"] = {}
        self.data["temperature"][type] = data

        foo = Temperature(group, "Cel")
        print(foo)
    def _parsePressure(self, group, type):
        """
        Parses a pressure group
        """

        # Create the data array
        PPPP = group[1:5]
        data = { "available": True, "raw": group, "unit": "hPa" }
        if PPPP[1:4] == "///":
            data["available"] = False
        else:
            data["value"] = (int(PPPP) / 10) + (0 if int(PPPP) > 500 else 1000)
        self.data[type] = data
################################################################################
# FUNCTIONS
################################################################################
def _isGroupValid(group, length=5, allowSlashes=True, multipleGroups=False):
    """
    Checks if group is valid.
    In most cases, a valid group is 5 alphanumeric characters and/or slashes (/)
    """
    regexp_parts = ["\d"]
    if allowSlashes:
        regexp_parts.append("\/")
    if multipleGroups:
        regexp_parts.append(" ")
    regexp = "^[{}]{{{}}}$".format("".join(regexp_parts), length)
    return bool(re.match(regexp, group))
# def createDataArray(availability=True, raw=None, value=None, unit=None, values=None):
#     """Creates a data array from the given values"""
#     # Initialise the data array
#     data = {}
#     if availability: data["available"] = True
#     if raw is not None:   data["raw"]   = raw
#     if value is not None: data["value"] = value
#     if unit is not None:  data["unit"]  = unit
#     if values is not None:
#         for v in values: data[v] = values[v]
    #
    # # Return the data
    # return data
