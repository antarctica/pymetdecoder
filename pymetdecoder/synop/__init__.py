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
import sys, re, logging
import pymetdecoder
from . import observations as obs
RADIATION_TYPES = [
    "positive_net", "negative_net", "global_solar",
    "diffused_solar", "downward_long_wave", "upward_long_wave",
    "short_wave"
]
################################################################################
# REPORT CLASSES
################################################################################
class SYNOP(pymetdecoder.Report):
    def _decode(self, message):
        """
        Decodes the SYNOP and sets the data attribute with the information
        """
        # Initialise data attribute
        data = {}

        # Create iterator of the message components
        groups = iter(message.split())

        ### SECTION 0 ###
        try:
            # Get the message type
            data["station_type"] = obs.StationType().decode(next(groups))

            # Add callsign for non-AAXX stations
            if data["station_type"]["value"] != "AAXX":
                data["callsign"] = obs.Callsign().decode(next(groups))

            # Get date, time and wind indictator
            YYGGi = next(groups)
            if not self._is_valid_group(YYGGi):
                logging.warning(pymetdecoder.InvalidGroup(YYGGi))
            data["obs_time"] = obs.ObservationTime().decode(YYGGi[0:4])
            data["wind_indicator"] = obs.WindIndicator().decode(YYGGi[4])

            # Obtain the default time before observation, in accordance with
            # regulations 12.2.6.6.1 and 12.2.6.7.1
            try:
                hour = data["obs_time"]["hour"]["value"]
                if hour in [0, 6, 12, 18]:
                    def_time_before = { "value": 6, "unit": "h" }
                elif hour in [3, 9, 15, 21]:
                    def_time_before = { "value": 3, "unit": "h" }
                # elif hour % 2 == 0:
                #     def_time_before = { "value": 2, "unit": "h" },
                else:
                    def_time_before = { "value": 1, "unit": "h" }
            except Exception:
                def_time_before = None

            # Now add the station ID if it is an AAXX station. Otherwise, add the current position
            if data["station_type"]["value"] == "AAXX":
                group = next(groups)
                if not self._is_valid_group(group, allowSlashes=False):
                    raise pymetdecoder.DecodeError("{} is an invalid IIiii group".format(group))
                data["station_id"] = obs.StationID().decode(group)
                data["region"]     = obs.Region().decode(group)
            elif data["station_type"]["value"] == "BBXX":
                data["station_position"] = obs.StationPosition().decode(
                    "{} {}".format(next(groups), next(groups))
                )
                region = data["callsign"]["region"] if "region" in data["callsign"] else "SHIP"
                data["region"] = { "value": region }
            else: # OOXX
                data["station_position"] = obs.StationPosition().decode(
                    "{} {} {} {}".format(next(groups), next(groups), next(groups), next(groups))
                )

            # Set the country, where possible
            self.set_country(data)

            # If this section ends with NIL, that's the end of the SYNOP
            next_group = next(groups)
            if next_group == "NIL":
                return data

            ### SECTION 1 ###
            # Get precipitation indicator, weather indicator, base of lowest cloud and visibility
            if not self._is_valid_group(next_group):
                logging.warning(pymetdecoder.InvalidGroup(next_group))
                data["precipitation_indicator"] = None
                data["weather_indicator"] = None
                data["lowest_cloud_base"] = None
                data["visibility"] = None
            else:
                data["precipitation_indicator"] = obs.PrecipitationIndicator().decode(next_group[0:1], country=self.country)
                data["weather_indicator"] = obs.WeatherIndicator().decode(next_group[1:2])
                data["lowest_cloud_base"] = obs.LowestCloudBase().decode(next_group[2:3])
                data["visibility"] = obs.Visibility().decode(next_group[3:5])

            # Get cloud cover, wind direction and speed
            Nddff = next(groups)
            (cloud_cover, surface_wind) = (None, None)
            if not self._is_valid_group(Nddff):
                logging.warning(pymetdecoder.InvalidGroup(Nddff))
            else:
                cloud_cover = obs.CloudCover().decode(Nddff[0:1])
                surface_wind = obs.SurfaceWind().decode(Nddff[1:5])
                if surface_wind is not None and surface_wind["speed"] is not None:
                    surface_wind["speed"]["unit"] = data["wind_indicator"]["unit"] if data["wind_indicator"] is not None else None
            data["cloud_cover"] = cloud_cover
            data["surface_wind"] = surface_wind

            # If the raw wind speed was 99 units, then we have to check if the next group is 00fff
            # as this represents wind speeds of >99 units
            try:
                next_group = next(groups)
                if data["surface_wind"] is not None and "speed" in data["surface_wind"]:
                    if data["surface_wind"]["speed"] is not None and str(data["surface_wind"]["speed"]["value"]) == "99":
                        if re.match("^00\d{3}", next_group):
                            data["surface_wind"]["speed"]["value"] = int(next_group[2:5])
                            next_group = next(groups)
            except StopIteration:
                raise
            except Exception as e:
                raise pymetdecoder.DecodeError("Unable to decode wind speed group {}".format(next_group))

            # Parse the next group, based on the group header
            for i in range(1, 10):
                try:
                    if not re.match("^(222|333)", next_group):
                        header = int(next_group[0:1])
                    else:
                        header = None
                except ValueError as e:
                    logging.warning("{} is not a valid section 1 group".format(next_group))
                    next_group = next(groups)
                    continue
                if header == i:
                    if not self._is_valid_group(next_group):
                        logging.warning(pymetdecoder.InvalidGroup(next_group))
                        next_group = next(groups)
                        continue
                    if i == 1: # Air temperature
                        data["air_temperature"] = obs.Temperature().decode(next_group)
                    elif i == 2: # Dewpoint or relative humidity
                        sn = next_group[1:2]
                        if sn == "9":
                            data["relative_humidity"] = obs.RelativeHumidity().decode(next_group[2:5])
                        else:
                            data["dewpoint_temperature"] = obs.Temperature().decode(next_group)
                    elif i == 3: # Station pressure
                        data["station_pressure"] = obs.Pressure().decode(next_group[1:5])
                    elif i == 4: # Sea level pressure or geopotential
                        # Determine if this is pressure or geopotential height
                        a = next_group[1]
                        if a in ["0", "9", "/"]:
                            data["sea_level_pressure"] = obs.Pressure().decode(next_group[1:5])
                        elif a in ["1", "2", "5", "7", "8"]:
                            data["geopotential"] = obs.Geopotential().decode(next_group)
                    elif i == 5: # Pressure tendency
                        data["pressure_tendency"] = obs.PressureTendency().decode(next_group)
                    elif i == 6: # Precipitation
                        # Check that we are expecting precipitation information in section 3
                        # If not, raise error
                        try:
                            if data["precipitation_indicator"]["in_group_1"]:
                                data["precipitation_s1"] = obs.Precipitation().decode(next_group)
                            else:
                                raise Exception
                        except Exception:
                            logging.warning("Unexpected precipitation group found in section 1")
                            # raise pymetdecoder.DecodeError("Unexpected precipitation group found in section 1")
                    elif i == 7: # Present and past weather
                        if not self._is_valid_group(next_group):
                            logging.warning("{} is not a valid group (expecting 7wwWW)".format(next_group))
                            if "_error" not in data:
                                data["_error"] = []
                            data["_error"].append(next_group)
                            continue

                        # If the weather indicator says we're not including a group 7 code, yet we find one
                        # something went wrong somewhere
                        try:
                            if self.data["weatherIndicator"].value not in [1, 4, 7]:
                                logging.warning("Group 7 codes found, despite reported as being omitted (ix = {})".format(self.data["weatherIndicator"].value))
                        except AttributeError:
                            pass

                        # Create the data array
                        try:
                            hour = data["obs_time"]["hour"]["value"]
                        except Exception:
                            hour = None
                        data["present_weather"] = obs.Weather().decode(next_group[1:3], time_before=def_time_before, type="present")
                        data["past_weather"] = [
                            obs.Weather().decode(next_group[3:4], type="past"),
                            obs.Weather().decode(next_group[4:5], type="past")
                        ]
                    elif i == 8: # Cloud type and amount
                        data["cloud_types"] = obs.CloudType().decode(next_group)
                    elif i == 9: # Exact observation time
                        data["exact_obs_time"] = obs.ExactObservationTime().decode(next_group)
                    next_group = next(groups)
                elif header is not None and header < i:
                    next_group = next(groups)

            # ### SECTION 2 ###
            has_section_2 = False
            ice_groups = []
            if next_group[0:3] == "222":
                if not self._is_valid_group(next_group):
                    logging.warning(pymetdecoder.InvalidGroup(next_group))
                    next_group = next(groups)
                else:
                    data["displacement"] = obs.ShipDisplacement().decode(next_group)
                    next_group = next(groups)
                    has_section_2 = True

            # Initialise swell wave directions
            sw_dirs = None

            if has_section_2:
                for i in range(0, 9):
                    try:
                        if not re.match("^(ICE|333)$", next_group):
                            header = int(next_group[0:1])
                        else:
                            header = None
                    except ValueError as e:
                        logging.warning("{} is not a valid section 2 group".format(next_group))
                        next_group = next(groups)
                        continue

                    if header == i:
                        if not self._is_valid_group(next_group):
                            logging.warning(pymetdecoder.InvalidGroup(next_group))
                            next_group = next(groups)
                            continue
                        if i == 0: # Sea surface temperature
                            data["sea_surface_temperature"] = obs.SeaSurfaceTemperature().decode(next_group)
                        elif i == 1: # Period and height of waves (instrumental)
                            if "wind_waves" not in data:
                                data["wind_waves"] = []
                            data["wind_waves"].append(obs.WindWaves().decode(next_group, instrumental=True))
                        elif i == 2: # Period and height of wind waves
                            if "wind_waves" not in data:
                                data["wind_waves"] = []
                            data["wind_waves"].append(obs.WindWaves().decode(next_group, instrumental=False))
                        elif i == 3: # Swell wave directions
                            sw_dirs = next_group
                        elif i == 4 or i == 5:
                            if "swell_waves" not in data:
                                data["swell_waves"] = []
                            data["swell_waves"].append(
                                obs.SwellWaves().decode("{} {}".format(sw_dirs, next_group))
                            )
                        elif i == 6: # Ice accretion
                            data["ice_accretion"] = obs.IceAccretion().decode(next_group)
                        elif i == 7: # Accurate wave height
                            if "wind_waves" not in data:
                                data["wind_waves"] = []
                            data["wind_waves"].append(obs.WindWaves().decode(next_group, instrumental=True))
                        elif i == 8:
                            data["wet_bulb_temperature"] = obs.WetBulbTemperature().decode(next_group)
                        next_group = next(groups)

                # ICE groups
                if next_group == "ICE":
                    while next_group[0:3] != "333":
                        ice_groups.append(next_group)
                        next_group = next(groups)
                if len(ice_groups) > 0:
                    data["sea_land_ice"] = obs.SeaLandIce().decode(ice_groups)

            ### SECTION 3 ###
            group_9 = []
            group_5 = None
            group_6 = 0
            if next_group == "333":
                next_group = next(groups)
                last_header = None
                while True:
                    if re.match("^(555)$", next_group):
                        break
                    try:
                        header = int(next_group[0])
                    except Exception:
                        logging.warning(pymetdecoder.InvalidGroup(next_group))
                        next_group = next(groups)
                        continue
                    if last_header is not None and header < last_header and group_5 is None:
                        break

                    if (0 <= header <= 6) and group_5 is not None:
                        # Determine if we're expecting group 3 precipitation
                        if next_group.startswith("6") and data["precipitation_indicator"]["in_group_3"]:
                            data["precipitation_s3"] = obs.Precipitation().decode(next_group, tenths=False)
                            # group_5 = None
                            group_6 += 1

                            # print(data["precipitation_indicator"]["in_group_3"])

                        if group_5[2] == "3":
                            radiation_time = { "value": 1, "unit": "h" }
                            radiation_unit = "kJ/m2"
                        elif group_5[1] == "5":
                            radiation_time = { "value": 24, "unit": "h" }
                            radiation_unit = "J/cm2"
                        radiation = obs.Radiation().decode(next_group[1:5],
                            unit = radiation_unit,
                            time_before = radiation_time
                        )
                        matches = re.match("55[45]0([78])", group_5)
                        if matches:
                            if matches.group(1) == "7":
                                radiation_type = "net_short_wave"
                            else:
                                radiation_type = "direct_solar"
                        else:
                            radiation_type = RADIATION_TYPES[header]
                        group_5 = None
                        if "radiation" not in data:
                            data["radiation"] = {}
                        if radiation_type not in data["radiation"]:
                            data["radiation"][radiation_type] = []
                        data["radiation"][radiation_type].append(radiation)
                        # logging.warning("parse group 5: {} (last: {})".format(next_group, group_5))
                        # group_5 = None
                    else:
                        if header == 0:
                            if data["region"] is None:
                                logging.warning("No region information found")
                            elif data["region"]["value"] == "Antarctic":
                                # TODO: tidy this up a bit
                                data["max_wind"] = obs.SurfaceWind().decode(next_group[1:5])
                                data["max_wind"]["speed"]["unit"] = data["surface_wind"]["speed"]["unit"]
                            elif data["region"]["value"] == "I":
                                data["ground_minimum_temperature"] = obs.GroundMinimumTemperature().decode(next_group[1:3])
                                data["local_precipitation"] = obs.LocalPrecipitation().decode(next_group[3:5])
                            else:
                                raise NotImplementedError("0xxxx is not valid for region {}".format(data["region"]["value"]))
                        elif header == 1:
                            data["maximum_temperature"] = obs.Temperature().decode(next_group)
                        elif header == 2:
                            data["minimum_temperature"] = obs.Temperature().decode(next_group)
                        elif header == 3:
                            if data["region"] is None:
                                logging.warning("No region information found")
                            elif not data["region"]["value"] in ["II", "III", "IV", "VI"]:
                                logging.warning("Ground state not measured in region {}".format(data["region"]["value"]))
                                next_group = next(groups)
                                continue
                            data["ground_state"] = obs.GroundState().decode(next_group)
                        elif header == 4:
                            data["ground_state_snow"] = obs.GroundStateSnow().decode(next_group)
                        elif header == 5:
                            if next_group.startswith("5") and len(next_group) == 5:
                                j = list(next_group)
                                if j[1] in ["0", "1", "2", "3"]: # 5[01234]xxx
                                    data["evapotranspiration"] = obs.Evapotranspiration().decode(next_group)
                                elif j[1] == "4": # 54xxx
                                    data["temperature_change"] = obs.TemperatureChange().decode(next_group[2:5])
                                elif j[1] == "5": # 55xxx
                                    if j[2] in ["0", "1", "2", "3"]: # 55[0123]xx
                                        data["sunshine"] = obs.Sunshine().decode(next_group)
                                        group_5 = next_group
                                    elif j[2] in ["4", "5"]: # 55[45]xx
                                        if next_group[3:5] not in ["07", "08"]:
                                            raise pymetdecoder.InvalidCode(next_group, "5jjjj")
                                        group_5 = next_group
                                    elif j[2] == "/": # 55/xx
                                        data["sunshine"] = obs.Sunshine().decode(next_group)
                                    else:
                                        raise pymetdecoder.InvalidCode(next_group, "section 3 group 5")
                                    group_5 = next_group
                                elif j[1] in ["6"]: # 56xxx
                                    data["cloud_drift_direction"] = obs.CloudDriftDirection().decode(next_group)
                                elif j[1] in ["7"]: # 57xxx
                                    data["cloud_elevation"] = obs.CloudElevation().decode(next_group)
                                elif j[1] in ["8", "9"]: # 5[89]xxx
                                    data["pressure_change"] = obs.PressureChange().decode(next_group)
                        elif header == 6:
                            # Check that we are expecting precipitation information in section 3
                            # If not, raise error
                            group_6 += 1
                            try:
                                if "precipitation_indicator" not in data or data["precipitation_indicator"] is None:
                                    logging.warning("No precipitation indicator information found")
                                elif data["precipitation_indicator"]["in_group_3"]:
                                    data["precipitation_s3"] = obs.Precipitation().decode(next_group, tenths=False)
                                else:
                                    logging.warning("Unexpected precipitation group found in section 3")
                            # except TypeError:
                                # This happens when an invalid precipitation indicator group was specified earlier
                                # logging.warning("No precipitation indicator information found")
                            except Exception:
                                raise pymetdecoder.DecodeError("Unexpected precipitation group found in section 3")
                        elif header == 7:
                            if data["region"] is None:
                                logging.warning("No region information found")
                            elif data["region"]["value"] == "Antarctic":
                                data["prevailing_wind"] = obs.DirectionCardinal().decode(next_group[1])
                                data["cloud_drift_direction"] = obs.CloudDriftDirection().decode(next_group)
                            else:
                                # probably want this in a different key/value pair?
                                data["precipitation_24h"] = obs.Precipitation().decode(next_group, tenths=True) # tenths of mm
                        elif header == 8:
                            if "cloud_layer" not in data:
                                data["cloud_layer"] = []
                            data["cloud_layer"].append(obs.CloudLayer().decode(next_group))
                        elif header == 9:
                            if next_group.startswith("9") and len(next_group) == 5:
                                group_9.append(next_group)
                    last_header = header
                    next_group = next(groups)

                # Remove unneeded radiation groups. This is not an elegant solution,
                # but it works
                if group_6 == 1:
                    if "precipitation_s3" in data and "radiation" in data:
                        del(data["radiation"])

            # Parse group 9 before moving on
            if len(group_9) > 0:
                data = self._parse_group_9(data, group_9, def_time_before)
                group_9 = []

            ### SECTION 4 ###
            if next_group == "444":
                data["section4"] = []
                next_group = next(groups)
                last_header = None
                while True:
                    if re.match("^(555)$", next_group):
                        break
                    data["section4"].append(next_group)
                    next_group = next(groups)
            else:
                if next_group != "555":
                    logging.warning("{} is not a valid group".format(next_group))
                    next_group = next(groups)

            ### SECTION 5 ###
            if next_group == "555":
                data["section5"] = []
                next_group = next(groups)
                # last_header = None
                while True:
                    # header = int(next_group[0])
                    # if last_header is not None and header < last_header:
                        # break
                    data["section5"].append(next_group)
                    next_group = next(groups)
        except StopIteration:
            # If we have reached this point with iceGroups or group 9 still intact, parse them
            try:
                if len(ice_groups) > 0:
                    data["sea_land_ice"] = obs.SeaLandIce().decode(ice_groups)
                if len(group_9) > 0:
                    data = self._parse_group_9(data, group_9, def_time_before)
            except UnboundLocalError as e:
                pass
            # return data

        # Add any not-implemented codes
        if len(self.not_implemented) > 0:
            data["_not_implemented"] = self.not_implemented

        # Return the data
        return data
    def _encode(self, data, **kwargs):
        """
        Encodes the SYNOP from data
        """
        # Set flags

        # Check if we're using the 90-99 values for visibility and cloud layers
        if "visibility" in data and data["visibility"] is not None:
            useVis90 = data["visibility"]["use90"] if "use90" in data["visibility"] else kwargs.get("useVis90", False)
        else:
            useVis90 = kwargs.get("useVis90", False)
        if "cloud_layer" in data and data["cloud_layer"] is not None:
            useCloud90 = data["cloud_layer"]["use90"] if "use90" in data["cloud_layer"] else kwargs.get("useCloud90", False)
        else:
            useCloud90 = kwargs.get("useCloud90", False)


        groups = []
        parsed = ["region"] # pre-populate with stuff we don't need to re-encode

        ### SECTION 0
        _section0 = [
            ("station_type", obs.StationType, {}),
            ("callsign", obs.Callsign, {}),
            [("obs_time", obs.ObservationTime, {}), ("wind_indicator", obs.WindIndicator, {})],
            ("station_id", obs.StationID, {}),
            ("station_position", obs.StationPosition, { "obs_type": data["station_type"]["value"], "allow_none": True })
        ]
        for s in _section0:
            if isinstance(s, tuple):
                s = [s]
            group = []
            for x in s:
                if x[0] in data:
                    # if "value" in data[x[0]]:
                    #     val = data[x[0]]["value"]
                    # else:
                    #     val = data[x[0]]
                    group.append(x[1]().encode(data[x[0]], **x[2]))
            if len(group) > 0:
                groups.append("".join(group))

        ### SECTION 1
        has_section_1 = False
        if "precipitation_indicator" in data:
            has_section_1 = True
        if not has_section_1:
            groups.append("NIL")
        else:
            _section1 = [
                [
                    ("precipitation_indicator", obs.PrecipitationIndicator, {}, True),
                    ("weather_indicator", obs.WeatherIndicator, {}, True),
                    ("lowest_cloud_base", obs.LowestCloudBase, {}, True),
                    ("visibility", obs.Visibility, { "use90": useVis90 }, True)
                ],[
                    ("cloud_cover", obs.CloudCover, { "allow_none": True }, True),
                    ("surface_wind", obs.SurfaceWind, {}, True)
                ],
                ("air_temperature", obs.Temperature, { "group": "1" }, False),
                ("dewpoint_temperature", obs.Temperature, { "group": "2" }, False),
                ("relative_humidity", obs.RelativeHumidity, { "group": "29" }, False),
                ("station_pressure", obs.Pressure, { "group": "3" }, False),
                ("sea_level_pressure", obs.Pressure, { "group": "4" }, False),
                ("geopotential", obs.Geopotential, { "group": "4" }, False),
                ("pressure_tendency", obs.PressureTendency, { "group": "5" }, False),
                ("precipitation_s1", obs.Precipitation, { "group": "6" }, False),
                [
                    ("present_weather", obs.Weather, { "group": "7", "weather_type": "present" }, False),
                    ("past_weather", obs.Weather, { "weather_type": "past" }, False)
                ],
                ("cloud_types", obs.CloudType, { "group": "8" }, False),
                ("exact_obs_time", obs.ExactObservationTime, { "group": "9" }, False)
            ]
            for s in _section1:
                if isinstance(s, tuple):
                    s = [s]
                group = []
                for x in s:
                    if x[0] in data:
                        if data[x[0]] is None:
                            val = None
                        val = data[x[0]]
                        # elif "value" in data[x[0]]:
                        #     val = data[x[0]]["value"]
                        # else:
                        #     val = data[x[0]] if x[0] in data else None
                        # if (val is None and x[3]) or val is not None:
                        group.append(x[1]().encode(val, **x[2]))
                    else:
                        if x[3]:
                            raise pymetdecoder.EncodeError("Required variable '{}' is missing".format(x[0]))
                            return None
                if len(group) > 0:
                    groups.append("".join(group))

        ### SECTION 2
        has_section_2 = False
        if "displacement" in data:
            groups.append(obs.ShipDisplacement().encode(data["displacement"], group="222", allow_none=True))
            has_section_2 = True

        # Only encode rest of section 2 if required
        if has_section_2:
            _section2 = [
                ("sea_surface_temperature", obs.SeaSurfaceTemperature, { "group": "0", "allow_none": True }, False),
                ("wind_waves", obs.WindWaves, { "_group": "1" }, False),
                ("wind_waves", obs.WindWaves, { "_group": "2" }, False),
                ("swell_waves", obs.SwellWaves, {}, False),
                ("ice_accretion", obs.IceAccretion, { "group": "6" }, False),
                ("wind_waves", obs.WindWaves, { "_group": "7" }, False),
                ("wet_bulb_temperature", obs.WetBulbTemperature, { "group": "8" }, False),
                ("sea_land_ice", obs.SeaLandIce, {}, False)
            ]
            for s in _section2:
                if isinstance(s, tuple):
                    s = [s]
                group = []
                for x in s:
                    if x[0] in data:
                        if data[x[0]] is None:
                            val = None
                        val = data[x[0]]
                        group.append(x[1]().encode(val, **x[2]))
                    else:
                        if x[3]:
                            raise pymetdecoder.EncodeError("Required variable '{}' is missing".format(x[0]))
                            return None
                group = list(filter(lambda a: a is not None, group))
                if len(group) > 0:
                    groups.append("".join(group))

        ### SECTION 3
        try:
            weather_time = data["present_weather"]["time_before_obs"]
        except:
            weather_time = None
        s3_groups = []
        if "max_wind" in data:
            if data["region"]["value"] == "Antarctic":
                s3_groups.append(obs.SurfaceWind().encode(data["max_wind"], group="0"))
            else:
                raise pymetdecoder.EncodeError("max_wind not valid for region {}".format(data["region"]["value"]))
        if "ground_minimum_temperature" in data or "local_precipitation" in data:
            if data["region"]["value"] == "I":
                s3_groups.append("0{}{}".format(
                    obs.GroundMinimumTemperature().encode(data["ground_minimum_temperature"]),
                    obs.LocalPrecipitation().encode(data["local_precipitation"])
                ))
            else:
                raise pymetdecoder.EncodeError("ground_minimum_temperature and local_precipitation not valid for region {}".format(data["region"]["value"]))
        if "maximum_temperature" in data:
            s3_groups.append(obs.Temperature().encode(data["maximum_temperature"], group="1"))
        if "minimum_temperature" in data:
            s3_groups.append(obs.Temperature().encode(data["minimum_temperature"], group="2"))
        if "ground_state" in data:
            s3_groups.append(obs.GroundState().encode(data["ground_state"], group="3"))
        if "ground_state_snow" in data:
            s3_groups.append(obs.GroundStateSnow().encode(data["ground_state_snow"], group="4"))
        if "evapotranspiration" in data:
            s3_groups.append(obs.Evapotranspiration().encode(data["evapotranspiration"], group="5"))
        if "temperature_change" in data:
            s3_groups.append(obs.TemperatureChange().encode(data["temperature_change"], group="54"))
        if "sunshine" in data:
            sunshine = obs.Sunshine().encode(data["sunshine"], group="55")
            s3_groups.append(sunshine)
            if "radiation" in data:
                radiation_time = 1 if sunshine[3] == "3" else 24
                for r, rad in data["radiation"].items():
                    for x in rad:
                        if "time_before_obs" in x and x["time_before_obs"]["value"] == radiation_time:
                            s3_groups.append(obs.Radiation().encode(x, group=str(RADIATION_TYPES.index(r))))
        if "radiation" in data and "sunshine" not in data:
            for r, rad in data["radiation"].items():
                for x in rad:
                    if "time_before_obs" in x:
                        if x["time_before_obs"]["value"] == 1:
                            prefix = "4"
                        elif x["time_before_obs"]["value"] == 24:
                            prefix = "5"
                        else:
                            continue
                        if r == "net_short_wave":
                            suffix = "7"
                        elif r == "direct_solar":
                            suffix = "8"
                        else:
                            continue
                        s3_groups.append("55{}0{}".format(prefix, suffix))
                        s3_groups.append(obs.Radiation().encode(x, group=prefix))
        if "cloud_drift_direction" in data and "prevailing_wind" not in data:
            s3_groups.append(obs.CloudDriftDirection().encode(data["cloud_drift_direction"], group="56"))
        if "cloud_elevation" in data:
            s3_groups.append(obs.CloudElevation().encode(data["cloud_elevation"], group="57"))
        if "pressure_change" in data:
            s3_groups.append(obs.PressureChange().encode(data["pressure_change"], group="5"))
        if "precipitation_s3" in data:
            val = data["precipitation_s3"]
            if "time_before_obs" in val and val["time_before_obs"] == { "value": 24, "unit": "h" }:
                s3_groups.append(obs.Precipitation().encode(data["precipitation_s3"]))
            else:
                s3_groups.append(obs.Precipitation().encode(data["precipitation_s3"], group="6"))
        if "precipitation_24h" in data:
            s3_groups.append(obs.Precipitation().encode(data["precipitation_24h"], group="7", is_24h=True))
        if "prevailing_wind" in data:
            s3_groups.append("7{wind}{drift}".format(
                wind = obs.DirectionCardinal().encode(data["prevailing_wind"], allow_none=True),
                drift = obs.CloudDriftDirection().encode(data["cloud_drift_direction"] if "cloud_drift_direction" in data else None)
            ))
        if "cloud_layer" in data:
            s3_groups.append(obs.CloudLayer().encode(data["cloud_layer"], use90=useCloud90))
        if "weather_info" in data:
            if "time_before_obs" in data["weather_info"]:
                s3_groups.append(obs.TimeBeforeObs().encode(data["weather_info"]["time_before_obs"], group="900"))
            if "variability" in data["weather_info"]:
                s3_groups.append(obs.VariableLocationIntensity().encode(data["weather_info"]["variability"], group="900"))
            if "non_persistent" in data["weather_info"]:
                s3_groups.append(obs.TimeBeforeObs().encode(data["weather_info"]["non_persistent"], group="905"))
        if "precipitation_begin" in data:
            s3_groups.append(obs.PrecipitationTime().encode(data["precipitation_begin"], group="909"))
        if "precipitation_end" in data:
            s3_groups.append(obs.PrecipitationTime().encode(data["precipitation_end"], group="909"))
        if "highest_gust" in data:
            s3_groups.append(obs.HighestGust().encode(data["highest_gust"], time_before=weather_time))
        if "mean_wind" in data:
            s3_groups.append(obs.MeanWind().encode(data["mean_wind"], time_before=weather_time))
        if "snow_fall" in data:
            s3_groups.append(obs.SnowFall().encode(data["snow_fall"], time_before=weather_time))
        if "sea_state" in data or "sea_visibility" in data:
            s3_groups.append("924{S}{V}".format(
                S = obs.SeaState().encode(data["sea_state"]),
                V = obs.SeaVisibility().encode(data["sea_visibility"])
            ))
        if "frozen_deposit" in data:
            s3_groups.append(obs.FrozenDeposit().encode(data["frozen_deposit"], group="927"))
        if "snow_cover_regularity" in data:
            s3_groups.append(obs.SnowCoverRegularity().encode(data["snow_cover_regularity"], group="928"))
        if "drift_snow" in data:
            s3_groups.append(obs.DriftSnow().encode(data["drift_snow"], group="929"))
        if "deposit_diameter" in data:
            for d in data["deposit_diameter"]:
                s3_groups.append(obs.DepositDiameter().encode(d, group="93"))
        if "cloud_evolution" in data:
            for d in data["cloud_evolution"]:
                s3_groups.append(obs.CloudEvolution().encode(d, group="940"))
        if "max_low_cloud_concentration" in data:
            for d in data["max_low_cloud_concentration"]:
                s3_groups.append(obs.MaxLowCloudConcentration().encode(d, group="944"))
        if "mountain_condition" in data:
            s3_groups.append(obs.MountainCondition().encode(data["mountain_condition"], group="950"))
        if "valley_clouds" in data:
            s3_groups.append(obs.ValleyClouds().encode(data["valley_clouds"], group="951"))
        if "present_weather_additional" in data:
            for idx, w in enumerate(data["present_weather_additional"]):
                if idx >= 2:
                    break
                s3_groups.append(obs.Weather().encode(w, group="96{}".format(idx), weather_type="present"))
        if "important_weather" in data:
            for idx, w in enumerate(data["important_weather"]):
                if idx >= 2:
                    break
                s3_groups.append(obs.ImportantWeather().encode(w, group="96{}".format(idx + 4)))
        if "present_weather" in data and data["present_weather"] is not None:
            if "location" in data["present_weather"]:
                s3_groups.append(obs.LocationMaxConcentration().encode(data["present_weather"]["location"], group="970"))
            if "movement" in data["present_weather"]:
                s3_groups.append(obs.PhenomSpeedDir().encode(data["present_weather"]["movement"], group="975"))
        if "present_weather_additional" in data and data["present_weather_additional"] is not None:
            for idx, w in enumerate(data["present_weather_additional"]):
                if idx >= 2:
                    break
                if "location" in w:
                    s3_groups.append(obs.LocationMaxConcentration().encode(w["movement"], group="97{}".format(idx + 1)))
                if "movement" in w:
                    s3_groups.append(obs.PhenomSpeedDir().encode(w["movement"], group="97{}".format(idx + 6)))
        if "past_weather" in data and data["past_weather"] is not None:
            for idx, w in enumerate(data["past_weather"]):
                if w is None:
                    continue
                if idx >= 2:
                    break
                if "location" in w:
                    s3_groups.append(obs.LocationMaxConcentration().encode(w["movement"], group="97{}".format(idx + 3)))
                if "movement" in w:
                    s3_groups.append(obs.PhenomSpeedDir().encode(w["movement"], group="97{}".format(idx + 8)))
        if "visibility_direction" in data:
            for d in data["visibility_direction"]:
                s3_groups.append(obs.VisibilityDirection().encode(d, group="98"))
        if "optical_phenomena" in data:
            s3_groups.append(obs.OpticalPhenomena().encode(data["optical_phenomena"], group="990"))
        if "mirage" in data:
            s3_groups.append(obs.Mirage().encode(data["mirage"], group="991"))
        if "st_elmos_fire" in data:
            s3_groups.append("99190")
        if "condensation_trails" in data:
            s3_groups.append(obs.CondensationTrails().encode(data["condensation_trails"], group="992"))
        if "special_clouds" in data:
            s3_groups.append(obs.SpecialClouds().encode(data["special_clouds"], group="993"))
        if "day_darkness" in data:
            s3_groups.append(obs.DayDarkness().encode(data["day_darkness"], group="994"))
        if "sudden_temperature_change" in data:
            s3_groups.append(obs.SuddenTemperatureChange().encode(data["sudden_temperature_change"],
                group = "996" if data["sudden_temperature_change"]["value"] > 0 else "997"
            ))
        if "sudden_humidity_change" in data:
            s3_groups.append(obs.SuddenHumidityChange().encode(data["sudden_humidity_change"],
                group = "998" if data["sudden_humidity_change"]["value"] > 0 else "999"
            ))
            # if len(group) > 0:
                # s3_groups.append("".join(group))
        if len(s3_groups) > 0:
            groups.extend(["333"] + s3_groups)

        ### SECTION 5
        if "section5" in data:
            groups.extend(["555"] + data["section5"])

        # Return the encoded report
        return " ".join(groups)

    # Functions to decode individual groups
    def _parse_sequential_group(self, data, min, max, groups, next_group, section, skip_re):
        for i in range(min, max):
            try:
                if not re.match(skip_re, next_group):
                    header = int(next_group[0:1])
                else:
                    header = None
            except ValueError as e:
                logging.warning("{} is not a valid section 1 group".format(next_group))
                next_group = next(groups)
                continue

            if header == i:
                info = section[int(i)]
                this_info = None
                for n in info:
                    if len(n[2]) == 0:
                        this_info = n
                        break
                    elif next_group[1] in n[2]:
                        this_info = n
                        break
                if this_info is None:
                    continue
                    # raise Exception("cannot determine (header: {}, group: {})".format(header, next_group))
                if not self._is_valid_group(next_group):
                    logging.warning("{} is an invalid {} group".format(next_group, this_info[0]))
                    next_group = next(groups)
                    continue

                multiple = this_info[3]["_multiple"] if "_multiple" in this_info[3] else False
                if isinstance(this_info[1], type):
                    value = this_info[1]().decode(next_group, **this_info[3])
                    if multiple:
                        if this_info[0] not in data:
                            data[this_info[0]] = []
                        data[this_info[0]].append(value)
                    else:
                        data[this_info[0]] = value
                elif callable(this_info[1]):
                    output = this_info[1](next_group, data, **this_info[3])
                    for idx, a in enumerate(this_info[0]):
                        data[a] = output[idx]
                next_group = next(groups)
            elif header is not None and header < i:
                next_group = next(groups)
        return (data, next_group)
    def _parse_group_9(self, data, group_9, def_time_before):
        """
        Parses group 9 codes
        """
        time_before_obs = def_time_before
        for idx, g in enumerate(group_9):
            j = list(g)
            if j[1] == "0":
                if j[2] == "0":
                    if "weather_info" not in data:
                        data["weather_info"] = {}
                    tz = g[3:5]
                    if tz != "//":
                        if 0 <= int(tz) <= 75:
                            data["weather_info"]["time_before_obs"] = obs.TimeBeforeObs().decode(tz)
                        else:
                            data["weather_info"]["variability"] = obs.VariableLocationIntensity().decode(tz)
                elif j[2] == "1":
                    if "weather_info" not in data:
                        data["weather_info"] = {}
                    tt = g[3:5]
                    data["weather_info"]["time_of_ending"] = obs.TimeOfEnding().decode(tt)
                elif j[2] == "5":
                    if "weather_info" not in data:
                        data["weather_info"] = {}
                    data["weather_info"]["non_persistent"] = obs.TimeBeforeObs().decode(g[3:5])
                elif j[2] == "7":
                    # Ignore if next group begins with 910, since 907 doesn't apply
                    try:
                        if group_9[idx + 1].startswith("910"):
                            continue
                    except Exception:
                        continue
                    time_before_obs = obs.TimeBeforeObs().decode(g[3:5])
                elif j[2] == "9":
                    # Check present weather. If present weather is >= 50, this is the beginning
                    # Otherwise, this is the end of precipitation
                    try:
                        if data["present_weather"]["value"] >= 50:
                            attr = "precipitation_begin"
                        else:
                            attr = "precipitation_end"
                    except:
                        attr = "precipitation_end"
                    data[attr] = obs.PrecipitationTime().decode(g)
                else:
                    self.handle_not_implemented(g)
            elif j[1] == "1":
                if j[2] == "0":
                    if "highest_gust" not in data:
                        data["highest_gust"] = []
                    data["highest_gust"].append(obs.HighestGust().decode(g,
                        unit = data["wind_indicator"]["unit"] if data["wind_indicator"] is not None else None,
                        measure_period = { "value": 10, "unit": "min" }
                    ))
                elif j[2] == "1":
                    # try:
                    #     time_before = time_before_obs
                    # except Exception:
                    #     time_before = def_time_before
                    # Check for direction
                    parse = [g]
                    try:
                        if group_9[idx + 1].startswith("915"):
                            parse.append(group_9[idx + 1])
                            group_9.pop(idx + 1)
                    except IndexError:
                        pass

                    if "highest_gust" not in data:
                        data["highest_gust"] = []
                    data["highest_gust"].append(obs.HighestGust().decode(" ".join(parse),
                        unit = data["wind_indicator"]["unit"] if data["wind_indicator"] is not None else None,
                        time_before = time_before_obs
                    ))
                else:
                    self.handle_not_implemented(g)
            elif j[1] == "2":
                if j[2] == "4":
                    data["sea_state"] = obs.SeaState().decode(g[3])
                    data["sea_visibility"] = obs.SeaVisibility().decode(g[4])
                elif j[2] == "7":
                    data["frozen_deposit"] = obs.FrozenDeposit().decode(g)
                elif j[2] == "8":
                    data["snow_cover_regularity"] = obs.SnowCoverRegularity().decode(g)
                elif j[2] == "9":
                    data["drift_snow"] = obs.DriftSnow().decode(g)
                else:
                    self.handle_not_implemented(g)
            elif j[1] == "3":
                if j[2] == "1":
                    # try:
                    #     time_before = time_before_obs
                    # except Exception:
                    #     time_before = def_time_before
                    data["snow_fall"] = obs.SnowFall().decode(g,
                        time_before = time_before_obs
                    )
                elif j[2] in ["3", "4", "5", "6", "7"]:
                    if "deposit_diameter" not in data:
                        data["deposit_diameter"] = []
                    data["deposit_diameter"].append(obs.DepositDiameter().decode(g))
                else:
                    self.handle_not_implemented(g)
            elif j[1] == "4":
                if j[2] == "0":
                    if "cloud_evolution" not in data:
                        data["cloud_evolution"] = []
                    data["cloud_evolution"].append(obs.CloudEvolution().decode(g))
                elif j[2] == "4":
                    if "max_low_cloud_concentration" not in data:
                        data["max_low_cloud_concentration"] = []
                    data["max_low_cloud_concentration"].append(obs.MaxLowCloudConcentration().decode(g))
                else:
                    self.handle_not_implemented(g)
            elif j[1] == "5":
                if j[2] == "0":
                    data["mountain_condition"] = obs.MountainCondition().decode(g)
                elif j[2] == "1":
                    data["valley_clouds"] = obs.ValleyClouds().decode(g)
                elif j[2] in ["2", "3", "4", "5", "6", "7"]:
                    raise pymetdecoder.DecodeError("{} is not a valid code".format(g))
                else:
                    self.handle_not_implemented(g)
            elif j[1] == "6":
                if j[2] in ["0", "1"]:
                    if "present_weather_additional" not in data:
                        data["present_weather_additional"] = []
                    weather = obs.Weather().decode(g[3:5], time_before=def_time_before, type="present")
                    data["present_weather_additional"].append(weather)
                elif j[2] in ["4", "5"]:
                    if "important_weather" not in data:
                        data["important_weather"] = []
                    use_4687 = True if j[2] == "5" else False
                    data["important_weather"].append(
                        obs.ImportantWeather().decode(g[3:5], time_before=def_time_before, use_4687=use_4687)
                    )
                else:
                    self.handle_not_implemented(g)
            elif j[1] == "7":
                if j[2] in ["0", "1", "2", "3", "4"]:
                    loc_max_concentration = obs.LocationMaxConcentration().decode(g)
                    try:
                        if j[2] == "0":
                            data["present_weather"]["location"] = loc_max_concentration
                        elif j[2] == "1":
                            data["present_weather_additional"][0]["location"] = loc_max_concentration
                        elif j[2] == "2":
                            data["present_weather_additional"][1]["location"] = loc_max_concentration
                        elif j[2] == "3":
                            data["past_weather"][0]["location"] = loc_max_concentration
                        elif j[2] == "4":
                            data["past_weather"][1]["location"] = loc_max_concentration
                    except KeyError as err:
                        logging.warning("Cannot decode {} - {} is missing".format(g, str(err)))
                elif j[2] in ["5", "6", "7", "8", "9"]:
                    speed_and_dir = obs.PhenomSpeedDir().decode(g)
                    try:
                        if j[2] == "5":
                            data["present_weather"]["movement"] = speed_and_dir
                        elif j[2] == "6":
                            data["present_weather_additional"][0]["movement"] =speed_and_dir
                        elif j[2] == "7":
                            data["present_weather_additional"][1]["movement"] = speed_and_dir
                        elif j[2] == "8":
                            data["past_weather"][0]["movement"] = speed_and_dir
                        elif j[2] == "9":
                            data["past_weather"][1]["movement"] = speed_and_dir
                    except KeyError as err:
                        logging.warning("Cannot decode {} - {} is missing".format(g, str(err)))
                else:
                    self.handle_not_implemented(g)
            elif j[1] == "8":
                if "visibility_direction" not in data:
                    data["visibility_direction"] = []
                data["visibility_direction"].append(obs.VisibilityDirection().decode(g))
            elif j[1] == "9":
                if j[2] == "0":
                    data["optical_phenomena"] = obs.OpticalPhenomena().decode(g)
                elif j[2] == "1":
                    if g[3:5] == "90":
                        data["st_elmos_fire"] = True
                    else:
                        data["mirage"] = obs.Mirage().decode(g)
                elif j[2] == "2":
                    data["condensation_trails"] = obs.CondensationTrails().decode(g)
                elif j[2] == "3":
                    data["special_clouds"] = obs.SpecialClouds().decode(g)
                elif j[2] == "4":
                    data["day_darkness"] = obs.DayDarkness().decode(g)
                elif j[2] in ["6", "7"]:
                    data["sudden_temperature_change"] = obs.SuddenTemperatureChange().decode(g[2:5])
                elif j[2] in ["8", "9"]:
                    data["sudden_humidity_change"] = obs.SuddenHumidityChange().decode(g[2:5])
                else:
                    self.handle_not_implemented(g)
            else:
                self.handle_not_implemented(g)
        return data
    def _is_valid_group(self, group, length=5, allowSlashes=True, multipleGroups=False):
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
        if len(group) != length:
            return False
        regexp_parts = ["\d"]
        if allowSlashes:
            regexp_parts.append("\/")
        if multipleGroups:
            regexp_parts.append(" ")
        regexp = "[{}]{{{}}}".format("".join(regexp_parts), length)
        return bool(re.match(regexp, group))
    def set_country(self, data):
        """
        Sets country where possible
        """
        self.country = None
        try:
            station_id = int(data["station_id"]["value"])

            # Find country
            if 20000 <= station_id <= 39999:
                self.country = "RU"
        except Exception:
            return
    def handle_not_implemented(self, code):
        """
        Handle non-implemented codes
        """
        self.not_implemented.append(code)
