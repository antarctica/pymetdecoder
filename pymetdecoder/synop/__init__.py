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
import re
import pymetdecoder
from . import section0
from . import section1
from . import section2
################################################################################
# REPORT CLASSES
################################################################################
class SYNOP(pymetdecoder.Report):
    def decode(self):
        """
        Decodes the SYNOP and sets the data attribute with the information
        """
        # Initialise data attribute
        self.data = {}

        # Create iterator of the message components
        groups = iter(self.message.split())

        ### SECTION 0 ###
        try:
            # Get the message type
            self.data["stationType"] = section0.StationType(next(groups))

            # Add callsign for non-AAXX stations
            if self.data["stationType"].value != "AAXX":
                self.data["callsign"] = section0.Callsign(next(groups))

            # Get date, time and wind indictator
            self.parseYYGGi(next(groups))

            # Now add the station ID if it is an AAXX station. Otherwise, add the current position
            if self.data["stationType"].value == "AAXX":
                group = next(groups)
                if not self._isGroupValid(group, allowSlashes=False):
                    raise pymetdecoder.DecodeError("{} is an invalid IIiii group".format(group))
                self.data["stationID"] = pymetdecoder.Observation(group, availability=False, value=group)
            elif self.data["stationType"].value == "BBXX":
                self.data["stationPosition"] = section0.StationPosition("{} {}".format(next(groups), next(groups)))
            else: # OOXX
                self.data["stationPosition"] = section0.StationPosition("{} {} {} {}".format(next(groups), next(groups), next(groups), next(groups)))

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

            # Parse the next group, based on the group header
            for i in range(1, 10):
                try:
                    header = int(next_group[0:1])
                except ValueError as e:
                    raise pymetdecoder.DecodeError("{} is not a valid section 1 group header".format(header))
                    break
                if header == i:
                    if i == 1: # Air temperature
                        self.data["airTemperature"] = section1.Temperature(next_group, "Cel")
                    elif i == 2: # Dewpoint or relative humidity
                        sn = next_group[1:2]
                        if sn == "9":
                            self.data["relativeHumidity"] = section1.RelativeHumidity(next_group, "%")
                        else:
                            self.data["dewpointTemperature"] = section1.Temperature(next_group, "Cel")
                    elif i == 3: # Station pressure
                        if not self._isGroupValid(next_group):
                            raise pymetdecoder.DecodeError("{} is an invalid station level pressure group".format(next_group))

                        # Create the data array
                        self.data["stationPressure"] = section1.Pressure(next_group, "hPa")
                    elif i == 4: # Sea level pressure or geopotential
                        self.parseSeaLevelPressureGeopotential(next_group)
                    elif i == 5: # Pressure tendency
                        if not self._isGroupValid(next_group):
                            raise pymetdecoder.DecodeError("{} is an invalid pressure tendency group".format(next_group))

                        # Create the data array
                        self.data["pressureTendency"] = section1.PressureTendency(next_group)
                    elif i == 6: # Precipitation
                        if not self._isGroupValid(next_group):
                            raise pymetdecoder.DecodeError("{} is an invalid precipitation group".format(next_group))

                        # Create the data array
                        self.data["precipitation"] = section1.Precipitation(next_group)
                    elif i == 7: # Present and past weather
                        if not self._isGroupValid(next_group):
                            raise pymetdecoder.DecodeError("{} is an invalid weather group".format(next_group))

                        # If the weather indicator says we're not including a group 7 code, yet we find one
                        # something went wrong somewhere
                        if self.data["weatherIndicator"].value not in [1, 4, 7]:
                            raise pymetdecoder.DecodeError("Group 7 codes found, despite reported as being omitted (ix = {})".format(self.data["weatherIndicator"].value))

                        # Create the data array
                        self.data["presentWeather"] = section1.Weather(next_group[1:3])
                        self.data["pastWeather"] = [
                            section1.Weather(next_group[3:4]),
                            section1.Weather(next_group[4:5])
                        ]
                    elif i == 8: # Cloud type and amount
                        if not self._isGroupValid(next_group):
                            raise pymetdecoder.DecodeError("{} is an invalid cloud type/amount group".format(next_group))

                        # Create the data array
                        self.data["cloudTypes"] = section1.CloudTypes(next_group)
                    elif i == 9: # Exact observation time
                        if not self._isGroupValid(next_group):
                            raise pymetdecoder.DecodeError("{} is an invalid exact observation time group".format(next_group))

                        # Create the data array
                        self.data["exactObsTime"] = section1.ExactObservationTime(next_group)
                    next_group = next(groups)

            ### SECTION 2 ###
            if next_group[0:3] == "222":
                self.data["displacement"] = section2.ShipDisplacement(next_group)
                next_group = next(groups)

                # Parse the next group, based on the group header
                for i in range(0, 9):
                    try:
                        header = int(next_group[0:1])
                    except ValueError as e:
                        raise pymetdecoder.DecodeError("{} is not a valid section 1 group header".format(header))
                        break
                    if header == i:
                        if i == 0: # Sea surface temperature
                            if not self._isGroupValid(next_group):
                                raise pymetdecoder.DecodeError("{} is an invalid sea surface temperature group".format(next_group))
                            self.data["seaSurfaceTemperature"] = section2.SeaSurfaceTemperature(next_group)
                        if i == 1: # Period and height of waves (instrumental)
                            if not self._isGroupValid(next_group):
                                raise pymetdecoder.DecodeError("{} is an invalid instrumental wave group".format(next_group))
                            if "waves" not in self.data:
                                self.data["waves"] = {}
                            if "wind" not in self.data["waves"]:
                                self.data["waves"]["wind"] = []
                            self.data["waves"]["wind"].append(section2.WindWaves(next_group, instrumental=True))
                        if i == 2: # Period and height of wind waves
                            if not self._isGroupValid(next_group):
                                raise pymetdecoder.DecodeError("{} is an invalid wind wave group".format(next_group))
                            if "waves" not in self.data:
                                self.data["waves"] = {}
                            if "wind" not in self.data["waves"]:
                                self.data["waves"]["wind"] = []
                            self.data["waves"]["wind"].append(section2.WindWaves(next_group, instrumental=False))
                        if i == 3: # Swell wave directions
                            if not self._isGroupValid(next_group):
                                raise pymetdecoder.DecodeError("{} is an invalid swell wave direction group".format(next_group))
                            swData = [next_group]
                            swGroups = [4]
                            # if next_group[1:3] != "//":
                            #     swGroups.append(4) # We are expecting group 4 data
                            if next_group[3:5] != "//":
                                swGroups.append(5) # We are expecting group 5 data
                        if i == 4 or i == 5: # Swell wave period and height
                            if not self._isGroupValid(next_group):
                                raise pymetdecoder.DecodeError("{} is an invalid swell wave group".format(next_group))
                            try:
                                swGroups
                            except NameError as e:
                                swGroups = []

                            swData.append(next_group)
                            if len(swData) == len(swGroups) + 1:
                                if "waves" not in self.data:
                                    self.data["waves"] = {}
                                self.data["waves"]["swell"] = section2.SwellWaves(" ".join(swData))
                        if i == 6: # Ice accretion
                            if not self._isGroupValid(next_group):
                                raise pymetdecoder.DecodeError("{} is an invalid ice accretion group".format(next_group))
                            self.data["iceAccretion"] = section2.IceAccretion(next_group)
                        if i == 7: # Accurate wave heights
                            if not self._isGroupValid(next_group):
                                raise pymetdecoder.DecodeError("{} is an invalid wave height group".format(next_group))
                            self.data["waves"]["wind"].append(section2.WindWaves(next_group, instrumental=True))
                        if i == 8: # Wet bulb temperature
                            if not self._isGroupValid(next_group):
                                raise pymetdecoder.DecodeError("{} is an invalid wet bulb temperature group".format(next_group))
                            self.data["wetBulbTemperature"] = section2.WetBulbTemperature(next_group, "Cel")
                        next_group = next(groups)

            # ICE groups
            iceGroups = []
            if next_group == "ICE":
                while next_group[0:3] != "333":
                    iceGroups.append(next_group)
                    next_group = next(groups)
            self.data["seaLandIce"] = section2.SeaLandIce(iceGroups)

            ### SECTION 3 ###
            if next_group[0:3] == "333":
                # print("doing section 3")
                pass


            # Determine next section
            # print(next_group[0:3])
            # if next_group[0:3] == "222":
            #     ### SECTION 2 ###
            #     print("do section 2 stuff")
            # elif next_group[0:3] == "333":
            #     # do section 3 stuff
            #     print("do section 3 stuff")
            # else:
            #     raise pymetdecoder.DecodeError("I'm not sure what to do with {}".format(next_group))

        except StopIteration:
            # If we have reached this point with iceGroups still intact, parse them
            try:
                self.data["seaLandIce"] = section2.SeaLandIce(iceGroups)
            except UnboundLocalError as e:
                pass
            return

    # Functions to decode individual groups
    def parseYYGGi(self, group): # YYGGi
        """
        Parses the observation time and wind indicator group (YYGGi) and sets
        the obsTime and windIndicator data values

        :param string group: SYNOP code to decode
        :raises: pymetdecoder.DecodeError if groups is not a valid YYGGi group
        """
        # Check group matches regular expression
        if not self._isGroupValid(group):
            raise pymetdecoder.DecodeError("{} is an invalid YYGGi group".format(group))

        # Add observation time to data
        self.data["obsTime"] = section0.ObservationTime(group[0:4])

        # Add wind indicator to data
        self.data["windIndicator"] = section0.WindIndicator(group[4])
    def parseiihVV(self, group): # iihVV
        """
        Parses the precipitation and weather indicator and cloud base group (iihVV)
        and sets the precipitationIndicator, weatherIndicator and lowestCloudBase
        data values

        :param string group: SYNOP code to decode
        :raises: pymetdecoder.DecodeError if groups is not a valid iihVV group
        """
        # Check group matches regular expression
        if not self._isGroupValid(group):
            raise pymetdecoder.DecodeError("{} is an invalid iihVV group".format(group))

        # Get the precipitation indicator (iR)
        self.data["precipitationIndicator"] = section1.PrecipitationIndicator(group[0:1])

        # Get the weather indicator (ix)
        self.data["weatherIndicator"] = section1.WeatherIndicator(group[1:2])

        # Get the lowest cloud base (h)
        self.data["lowestCloudBase"] = section1.LowestCloudBase(group[2:3], unit="m")

        # Get the horizonal visibility (VV)
        self.data["visibility"] = section1.Visibility(group[3:5], unit="m")
    def parseNddff(self, group): # Nddff
        """
        Parses the cloud cover and surface wind group (Nddff) and sets the cloudCover
        and surfaceWind data values

        :param string group: SYNOP code to decode
        :raises: pymetdecoder.DecodeError if groups is not a valid Nddff group
        """
        if not self._isGroupValid(group):
            raise pymetdecoder.DecodeError("{} is an invalid Nddff group".format(group))

        # Get total cloud cover (N)
        self.data["cloudCover"] = section1.CloudCover(group[0:1], unit="okta")

        # Get wind direction (dd) and wind speed (ff)
        self.data["surfaceWind"] = section1.SurfaceWind(group[1:5])
        if hasattr(self.data["surfaceWind"], "speed") and hasattr(self.data["windIndicator"], "unit"):
            self.data["surfaceWind"].speed.setUnit(self.data["windIndicator"].unit)
    def parseAirTemperature(self, group): # 1snTTT
        """
        Parses the air temperature group (1snTTT) and sets the air temperature
        data value

        :param string group: SYNOP code to decode
        :raises: pymetdecoder.DecodeError if groups is not a valid 1snTTT group
        """
        if not self._isGroupValid(group):
            raise pymetdecoder.DecodeError("{} is an invalid air temperature group".format(group))

        # Prepare the data
        if "temperature" not in self.data:
            self.data["temperature"] = {}
        self.data["temperature"]["air"] = section1.Temperature(group, "Cel")
    def parseDewpointHumidity(self, group): # 2snTTT or 29UUU
        """
        Parses the dewpoint temperature/relative humidity group (2snTTT or 29UUU)
        and sets the relativeHumidity and/or dewpoint temperature data values

        :param string group: SYNOP code to decode
        :raises: pymetdecoder.DecodeError if groups is not a valid dewpoint temperature/relative humidity group
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
            if "temperature" not in self.data:
                self.data["temperature"] = {}
            self.data["temperature"]["dewpoint"] = section1.Temperature(group, "Cel")
    def parseSeaLevelPressureGeopotential(self, group): # 4PPPP or 4ahhh
        """
        Parses the sea level pressure/geopotential group (4PPPP or 4ahhh) and sets
        the seaLevelPressure and/or geopotential data values

        :param string group: SYNOP code to decode
        :raises: pymetdecoder.DecodeError if groups is not a valid sea level pressure/geopotential group
        """
        if not self._isGroupValid(group):
            raise pymetdecoder.DecodeError("{} is an invalid sea level pressure/geopotential group".format(group))

        # Determine if this is pressure or geopotential height
        a = group[1]
        if a in ["0", "9"]:
            self.data["seaLevelPressure"] = section1.Pressure(group, "hPa")
        elif a in ["1", "2", "5", "7", "8", "/"]:
            self.data["geopotential"] = section1.Geopotential(group)
    def _isGroupValid(self, group, length=5, allowSlashes=True, multipleGroups=False):
        """
        Internal function to check if group is valid. In most cases, a valid group
        is 5 alphanumeric characters and/or slashes

        :param string group: SYNOP code to decode
        :param int length: Desired length of group
        :param boolean allowSlashes: Slashes (/) are allowed in this group
        :param boolean multipleGroups: Check for multiple groups
        :returns: True if group contains all valid characters and is correct length, False otherwise
        :rtype: boolean
        """
        regexp_parts = ["\d"]
        if allowSlashes:
            regexp_parts.append("\/")
        if multipleGroups:
            regexp_parts.append(" ")
        regexp = "[{}]{{{}}}".format("".join(regexp_parts), length)
        return bool(re.match(regexp, group))
