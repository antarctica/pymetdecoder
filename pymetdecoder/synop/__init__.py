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
################################################################################
# EXCEPTION CLASSES
################################################################################
class SYNOPError(Exception):
    pass
################################################################################
# REPORT CLASSES
################################################################################
class SYNOP(object):
    def __init__(self, message):
        """Initialises the SYNOP report object"""
        pymetdecoder.Report.__init__(self, message)

    # Decode the SYNOP
    def decode(self):
        """Decodes the SYNOP"""
        # Initialise data attribute
        self.data = {}

        # Create iterator of the message components
        groups = iter(self.message.split())

        ### SECTION 0 ###
        try:
            # Get the message type
            self.parseStationType(next(groups))

            # Add callsign for non-AAXX stations
            if self.data["stationType"]["value"] != "AAXX":
                self.parseCallsign(next(groups))

            # Get date, time and wind indictator
            self.parseYYGGi(next(groups))

            # Now add the station ID if it is an AAXX station. Otherwise, add the current position
            if self.data["stationType"]["value"] == "AAXX":
                self.parseStationID(next(groups))
            elif self.data["stationType"]["value"] == "BBXX":
                self.parseStationPosition("{} {}".format(next(groups), next(groups)))
            else: # OOXX
                self.parseStationPosition("{} {} {} {}".format(next(groups), next(groups), next(groups), next(groups)))

            # If this section ends with NIL, that's the end of the SYNOP
            next_group = next(groups)
            if next_group == "NIL":
                return

            ### SECTION 1 ###
            # Get precipitation indicator, weather indicator, base of lowest cloud and visibility
            self.parseiihVV(next_group)

            # Get cloud cover, wind direction and speed
            self.parseNddff(next(groups))

            # If the raw wind speed was 99 units, then we have to check if the next group is 00fff
            # as this represents wind speeds of >99 units
            next_group = next(groups)
            if self.data["surfaceWind"]["speed"]["raw"] == "99":
                if re.match("^00\d{3}", next_group):
                    self.data["surfaceWind"]["speed"]["value"] = int(next_group[2:5])
                    self.data["surfaceWind"]["speed"]["raw"] += " {}".format(next_group)
                    next_group = next(groups)

            # Parse the next group, based on the group header
            last_header = 0
            while True:
                header = int(next_group[0:1])
                if last_header >= header: # Groups are ascending, so if they're out of order, it's the end
                    break
                elif header == 1:
                    self.parseAirTemperature(next_group)
                elif header == 2:
                    self.parseDewpointHumidity(next_group)
                else:
                    break
                next_group = next(groups)
                last_header = header
        except StopIteration:
            return

    # Functions to decode individual groups
    def parseStationType(self, group): # MMMM
        """Parses the station type group (MMMM)"""
        if re.match("^(AA|BB|OO)XX$", group):
            self.data["stationType"] = { "value": group, "raw": group }
        else:
            raise SYNOPError("{} is an invalid station type".format(group))
    def parseCallsign(self, group): # D...D or A1bwnnn
        """Parses the callsign group (D...D or A1bwnnn)"""
        if re.match("^(1[1-7]|2[1-6]|3[1-4]|4[1-8]|5[1-6]|6[1-6]|7[1-4])\d{3}$", group):
            regions = ["I", "II", "III", "IV", "V", "VI", "Antarctic"]
            self.data["callsign"] = {
                "region": regions[int(group[0:1]) - 1],
                "id": group,
                "raw": group
            }
        elif re.match("^[A-Z\d]{3,}", group):
            self.data["callsign"] = { "id": group, "raw": group }
        else:
            raise SYNOPError("Unable to determine {} callsign information from {}".format(self.data["stationType"]["value"], group))
    def parseYYGGi(self, group): # YYGGi
        """Parses the observation time and wind indicator group (YYGGi)"""
        # Check group matches regular expression
        if not self._isGroupValid(group):
            raise SYNOPError("{} is an invalid YYGGi group".format(group))

        # Get the individual values
        YY = group[0:2]
        GG = group[2:4]
        iw = group[4]

        # Check observation time values are valid
        if int(YY) > 31:
            raise SYNOPError("{} is an invalid value for observation day (YY)".format(YY))
        if int(GG) > 24:
            raise SYNOPError("{} is an invalid value for observation hour (GG)".format(GG))

        # Add observation time to data
        self.data["obsTime"] = { "day": YY, "hour": GG, "raw": group[0:4] }

        # Check wind indicator is valid
        if not re.match("^[0134/]$", iw):
            raise SYNOPError("{} is an invalid value for the wind indicator (iw)".format(iw))

        # Add wind indicator to data
        data = { "available": True, "raw": iw }
        if iw == "/":
            data["available"] = False
        else:
            iw = int(iw)
            data["value"] = iw
            data["unit"]  = "m/s" if iw < 2 else "KT"
            data["estimated"] = True if iw in [0, 3] else False
        self.data["windIndicator"] = data
    def parseStationID(self, group): # IIiii
        """Parses the station ID (IIiii)"""
        # Check group matches regular expression
        if not self._isGroupValid(group, allowSlashes=False):
            raise SYNOPError("{} is an invalid IIiii group".format(group))
        self.data["stationID"] = { "id": group, "raw": group }
    def parseStationPosition(self, group): # 99LaLaLa QcLoLoLoLo
        """Parses the station position groups (99LaLaLa QcLoLoLoLo)"""
        # Check group matches regular expression
        if not self._isGroupValid(group, length=11, multipleGroups=True):
            raise SYNOPError("{} is an invalid 99LaLaLa QcLoLoLoLo group".format(group))

        # Set the data
        data = { "available": True }
        if re.match("^99/// /////", group):
            data["available"] = False
        else:
            LaLaLa   = int(group[2:5]) # latitude
            Qc       = int(group[6:7]) # quadrant
            LoLoLoLo = int(group[7:11]) # longitude
            data["latitude"]  = "{:.1f}".format(LaLaLa / (-10.0 if Qc in [3, 5] else 10.0))
            data["longitude"] = "{:.1f}".format(LoLoLoLo / (-10.0 if Qc in [5, 7] else 10.0))
            data["raw"]       = group[2:11]

        # The following is only for OOXX stations (MMMULaULo h0h0h0h0im)
        if self.data["stationType"]["value"] == "OOXX":
            MMM      = int(group[12:15]) # Marsden square
            ULa      = int(group[15:16]) # Latitude unit
            ULo      = int(group[16:17]) # Longitude unit
            h0h0h0h0 = int(group[18:22]) # Elevation
            im       = int(group[22:23]) # Elevation indicator/confidence
            if (not 1 <= MMM <= 623) and (not 901 <= MMM <= 936):
                raise SYNOPError("{} is not a valid Marsden Square".format(MMM))

            confidence = ["Poor", "Excellent", "Good", "Fair"]
            data["marsdenSquare"] = MMM
            data["elevation"] = h0h0h0h0
            data["elevationUnits"] = "m" if im <= 4 else "ft"
            data["confidence"] = confidence[im % 4]
            data["raw"] = group[2:23]

        # Add to data array
        self.data["stationPosition"] = data
    def parseiihVV(self, group): # iihVV
        """Parses the precipitation and weather indicator and cloud base group (iihVV)"""
        # Check group matches regular expression
        if not self._isGroupValid(group):
            raise SYNOPError("{} is an invalid iihVV group".format(group))

        # Get the precipitation indicator (iR)
        iR = group[0:1]
        data = { "available": True, "raw": iR }
        if iR != "/":
            iR = int(iR)
            data["value"] = iR
            data["inGroup1"] = True if iR in [0, 1] else False
            data["inGroup3"] = True if iR in [0, 2] else False
        else:
            data["available"] = False
        self.data["precipitationIndicator"] = data

        # Get the weather indicator (ix)
        ix = group[1:2]
        data = { "available": True, "raw": ix }
        if ix != "/":
            ix = int(ix)
            data["value"] = ix
            data["automatic"] = True if ix >= 4 else False
        else:
            data["available"] = False
        self.data["weatherIndicator"] = data

        # Get the lowest cloud base (h)
        h = group[2:3]
        minBase = [0, 50, 100, 200, 300, 600, 1000, 1500, 2000, 2500, float("inf")]
        data = { "available": True, "raw": h }
        if h != "/":
            h = int(h)
            data["min"] = minBase[h]
            data["max"] = minBase[h + 1]
            data["unit"] = "m"
        else:
            data["available"] = False
        self.data["lowestCloudBase"] = data

        # Get the horizonal visibility (VV)
        VV = group[3:5]
        if VV != "//":
            VV = int(VV)
            visibility = None
            quantifier = None
            if 51 <= VV <= 55:
                raise SYNOPError("{} is not a valid visibility code for code table 4377".format(VV))
            if VV == 0:
                visibility = 100
                quantifier = "isLess"
            elif VV <= 50: visibility = VV * 100
            elif VV <= 80: visibility = (VV - 50) * 1000
            elif VV <= 88: visibility = (VV - 74) * 5000
            elif VV == 89:
                visibility = 70000
                quantifier = "isGreater"
            elif VV == 90:
                visibility = 50
                quantifier = "isLess"
            elif VV == 91: visibility = 50
            elif VV == 92: visibility = 200
            elif VV == 93: visibility = 500
            elif VV == 94: visibility = 1000
            elif VV == 95: visibility = 2000
            elif VV == 96: visibility = 4000
            elif VV == 97: visibility = 10000
            elif VV == 98: visibility = 20000
            elif VV == 99:
                visibility = 50000
                quantifier = "isGreaterOrEqual"
            else:
                raise SYNOPError("{} is not a valid visibility code for code table 4377".format(VV))
            data = { "available": True, "unit": "m" }
            if visibility is not None:
                data["visibility"] = visibility
            if quantifier is not None:
                data["quantifier"] = quantifier
        else:
            data = { "available": False }
        data["raw"] = group[3:5]
        self.data["visibility"] = data
    def parseNddff(self, group): # Nddff
        """Parses the cloud cover and surface wind group (Nddff)"""
        if not self._isGroupValid(group):
            raise pymetdecoder.DecodeError("{} is an invalid Nddff group".format(group))

        # Get total cloud cover (N)
        N = group[0:1]
        data = { "raw": N, "available": True }
        if N == "/":
            data["available"] = False
        else:
            N = int(N)
            if N == 9:
                data["obscured"] = True
            else:
                data["value"] = N
                data["obscured"] = False
        self.data["cloudCover"] = data

        # Get wind direction (dd) and wind speed (ff)
        dd = group[1:3]
        ff = group[3:5]
        data = {
            "direction": { "raw": dd, "available": True },
            "speed":     { "raw": ff, "available": True }
        }
        if dd == "//":
            data["direction"]["available"] = False
        else:
            dd = int(dd)
            if dd == 0:
                data["direction"]["calm"] = True
            elif dd == 99:
                data["direction"]["varAllUnknown"] = True
            elif 1 <= dd <= 36:
                data["direction"]["value"] = dd * 10
            else:
                raise SYNOPError("{} is not a valid wind direction code for code table 0877".format(dd))
        if ff == "//":
            data["speed"]["available"] = False
        else:
            data["speed"]["value"] = int(ff)
            data["speed"]["unit"]  = self.data["windIndicator"]["unit"]
        self.data["surfaceWind"] = data
    def parseAirTemperature(self, group): # 1snTTT
        """Parses the air temperature group (1snTTT)"""
        if not self._isGroupValid(group):
            raise SYNOPError("{} is an invalid air temperature group".format(group))

        # Get sign and temperature
        sn  = group[1:2]
        TTT = group[2:5]

        # Prepare the data
        self._parseTemperature(group, sn, TTT, "air")
    def parseDewpointHumidity(self, group): # 2snTTT or 29UUU
        """Parses the dewpoint temperature/relative humidity group (2snTTT or 29UUU)"""
        if not self._isGroupValid(group):
            raise SYNOPError("{} is an invalid dewpoint temperature/relative humidity group".format(group))

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
                    raise SYNOPError("{} is not a valid relative humidity".format(TTT))
                data["unit"] = "%"
                data["value"] = TTT
            self.data["relativeHumidity"] = data
        else:
            self._parseTemperature(group, sn, TTT, "dewpoint")

    def _isGroupValid(self, group, length=5, allowSlashes=True, multipleGroups=False):
        """Checks if group is valid. In most cases, a valid group is 5 alphanumeric
        characters and/or slashes (/)"""
        regexp_parts = ["\d"]
        if allowSlashes:
            regexp_parts.append("\/")
        if multipleGroups:
            regexp_parts.append(" ")
        regexp = "[{}]{{{}}}".format("".join(regexp_parts), length)
        return bool(re.match(regexp, group))
    def _parseTemperature(self, group, sign, temperature, type):
        """Parses a temperature group"""

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
                raise SYNOPError("{} is not a valid temperature sign code for code table 3845".format(sign))

            # Add data
            data["unit"]  = "Cel"
            data["value"] = (temperature / 10.0) * (1 if sign == 0 else -1)
        if "temperature" not in self.data:
            self.data["temperature"] = {}
        self.data["temperature"][type] = data
################################################################################
# FUNCTIONS
################################################################################
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
