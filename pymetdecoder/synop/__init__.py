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
from . import section0
from . import section1
from . import section2
from . import section3
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
            data["station_type"] = section0._StationType().decode(next(groups))

            # Add callsign for non-AAXX stations
            if data["station_type"]["value"] != "AAXX":
                data["callsign"] = section0._Callsign().decode(next(groups))

            # Get date, time and wind indictator
            (obs_time, wind_indicator) = self._parseYYGGi(next(groups))
            data["obs_time"] = obs_time
            data["wind_indicator"] = wind_indicator

            # Obtain the default time before observation, in accordance with
            # regulations 12.2.6.6.1 and 12.2.6.7.1
            try:
                hour = data["obs_time"]["hour"]["value"]
                if hour in [0, 6, 12, 18]:
                    def_time_before = { "value": 6, "unit": "h" }
                elif hour in [3, 9, 15, 21]:
                    def_time_before = { "value": 3, "unit": "h" }
                elif hour % 2 == 0:
                    def_time_before = { "value": 2, "unit": "h" },
                else:
                    def_time_before = { "value": 1, "unit": "h" }
            except Exception:
                def_time_before = None

            # Now add the station ID if it is an AAXX station. Otherwise, add the current position
            if data["station_type"]["value"] == "AAXX":
                group = next(groups)
                if not self._isGroupValid(group, allowSlashes=False):
                    raise pymetdecoder.DecodeError("{} is an invalid IIiii group".format(group))
                data["station_id"] = section0._StationID().decode(group)
                data["region"]     = section0._Region().decode(group)
            elif data["station_type"]["value"] == "BBXX":
                data["station_position"] = section0._StationPosition().decode(
                    "{} {}".format(next(groups), next(groups))
                )
                region = data["callsign"]["region"] if "region" in data["callsign"] else "SHIP"
                data["region"] = { "value": region }
            else: # OOXX
                data["station_position"] = section0._StationPosition().decode(
                    "{} {} {} {}".format(next(groups), next(groups), next(groups), next(groups))
                )

            # If this section ends with NIL, that's the end of the SYNOP
            next_group = next(groups)
            if next_group == "NIL":
                return data

            ### SECTION 1 ###
            # Get precipitation indicator, weather indicator, base of lowest cloud and visibility
            (precip_ind, weather_ind, cloud_base, vis) = self._parseiihVV(next_group)
            data["precipitation_indicator"] = precip_ind
            data["weather_indicator"] = weather_ind
            data["lowest_cloud_base"] = cloud_base
            data["visibility"] = vis

            # Get cloud cover, wind direction and speed
            (cloud_cover, surface_wind) = self._parseNddff(next(groups),
                data["wind_indicator"]["unit"] if data["wind_indicator"] is not None else None
            )
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
                    if i == 1: # Air temperature
                        data["air_temperature"] = section1._Temperature().decode(next_group)
                    elif i == 2: # Dewpoint or relative humidity
                        sn = next_group[1:2]
                        if sn == "9":
                            data["relative_humidity"] = section1._RelativeHumidity().decode(next_group[2:5])
                        else:
                            data["dewpoint_temperature"] = section1._Temperature().decode(next_group)
                    elif i == 3: # Station pressure
                        data["station_pressure"] = section1._Pressure().decode(next_group[1:5])
                    elif i == 4: # Sea level pressure or geopotential
                        # Determine if this is pressure or geopotential height
                        a = next_group[1]
                        if a in ["0", "9", "/"]:
                            data["sea_level_pressure"] = section1._Pressure().decode(next_group[1:5])
                        elif a in ["1", "2", "5", "7", "8"]:
                            data["geopotential"] = section1._Geopotential().decode(next_group)
                    elif i == 5: # Pressure tendency
                        data["pressure_tendency"] = section1._PressureTendency().decode(next_group)
                    elif i == 6: # Precipitation
                        # Check that we are expecting precipitation information in section 3
                        # If not, raise error
                        try:
                            if data["precipitation_indicator"]["in_group_1"]:
                                data["precipitation_s1"] = section1._Precipitation().decode(next_group)
                        except Exception:
                            raise pymetdecoder.DecodeError("Unexpected precipitation group found in section 1")
                    elif i == 7: # Present and past weather
                        if not self._isGroupValid(next_group):
                            logging.warning("{} is not a valid group (expecting 7wwWW)".format(next_group))
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
                        data["present_weather"] = section1._Weather().decode(next_group[1:3], time_before=def_time_before)
                        data["past_weather"] = [
                            section1._Weather().decode(next_group[3:4]),
                            section1._Weather().decode(next_group[4:5])
                        ]
                    elif i == 8: # Cloud type and amount
                        data["cloud_types"] = section1._CloudType().decode(next_group)
                    elif i == 9: # Exact observation time
                        data["exact_obs_time"] = section1._ExactObservationTime().decode(next_group)
                    next_group = next(groups)
                elif header is not None and header < i:
                    next_group = next(groups)

            # ### SECTION 2 ###
            if next_group[0:3] == "222":
                data["displacement"] = section2._ShipDisplacement().decode(next_group)
                next_group = next(groups)

            # Initialise swell wave directions
            sw_dirs = None
            for i in range(0, 9):
                try:
                    if not re.match("^(ICE|333)$", next_group):
                        header = int(next_group[0:1])
                    else:
                        header = None
                except ValueError as e:
                    logging.warning("{} is not a valid section 2 group".format(next_group))
                    break

                if header == i:
                    if i == 0: # Sea surface temperature
                        data["sea_surface_temperature"] = section2._SeaSurfaceTemperature().decode(next_group)
                    elif i == 1: # Period and height of waves (instrumental)
                        if "wind_waves" not in data:
                            data["wind_waves"] = []
                        data["wind_waves"].append(section2._WindWaves().decode(next_group, instrumental=True))
                    elif i == 2: # Period and height of wind waves
                        if "wind_waves" not in data:
                            data["wind_waves"] = []
                        data["wind_waves"].append(section2._WindWaves().decode(next_group, instrumental=False))
                    elif i == 3: # Swell wave directions
                        sw_dirs = next_group
                    elif i == 4 or i == 5:
                        if sw_dirs is None:
                            logging.warning("Cannot decode swell wave group {} - no preceeding direction group".format(next_group))
                            continue
                        if "swell_waves" not in data:
                            data["swell_waves"] = []
                        data["swell_waves"].append(
                            section2._SwellWaves().decode("{} {}".format(sw_dirs, next_group))
                        )
                    elif i == 6: # Ice accretion
                        data["ice_accretion"] = section2._IceAccretion().decode(next_group)
                    elif i == 7: # Accurate wave height
                        if "wind_waves" not in data:
                            data["wind_waves"] = []
                        data["wind_waves"].append(section2._WindWaves().decode(next_group, instrumental=True))
                    elif i == 8:
                        data["wet_bulb_temperature"] = section2._WetBulbTemperature().decode(next_group)
                    next_group = next(groups)

            # ICE groups
            ice_groups = []
            if next_group == "ICE":
                while next_group[0:3] != "333":
                    ice_groups.append(next_group)
                    next_group = next(groups)
            if len(ice_groups) > 0:
                data["sea_land_ice"] = section2._SeaLandIce().decode(ice_groups)

            ### SECTION 3 ###
            if next_group == "333":
                next_group = next(groups)
                last_header = None
                while True:
                    if re.match("^(555)$", next_group):
                        break
                    header = int(next_group[0])
                    if last_header is not None and header < last_header:
                        break

                    if header == 0:
                        logging.warning("section 3 group 0")
                    elif header == 1:
                        data["maximum_temperature"] = section1._Temperature().decode(next_group)
                    elif header == 2:
                        data["minimum_temperature"] = section1._Temperature().decode(next_group)
                    elif header == 3:
                        if not data["region"]["value"] in ["II", "III", "IV", "VI"]:
                            logging.warning("Ground state not measured in region {}".format(data["region"]["value"]))
                            next_group = next(groups)
                            continue
                        data["ground_state"] = section3._GroundState().decode(next_group)
                    elif header == 4:
                        data["ground_state_snow"] = section3._GroundStateSnow().decode(next_group)
                    elif header == 5:
                        if next_group.startswith("5") and len(next_group) == 5:
                            j = list(next_group)
                            if j[1] in ["0", "1", "2", "3"]: # 5[01234]xxx
                                data["evapotranspiration"] = section3._Evapotranspiration().decode(next_group)
                            elif j[1] == "4": # 54xxx
                                raise NotImplementedError("54xxx is not implemented yet")
                            elif j[1] == "5": # 55xxx
                                if j[2] in ["0", "1", "2", "3"]: # 55[0123]xx
                                    data["sunshine"] = section3._Sunshine().decode(next_group)
                                elif j[2] in ["4", "5"]: # 55[45]xx
                                    raise NotImplementedError("55[45]xx is not implemented yet")
                                elif j[2] == "/": # 55/xx
                                    raise NotImplementedError("55/xx is not implemented yet")
#                                     self.data["sunshine"] = section3._sunshine(next_group)
                                else:
                                    raise Exception("bad sunshine")
                            elif j[1] in ["6"]: # 56xxx
                                data["cloud_drift_direction"] = section3._CloudDriftDirection().decode(next_group)
                            elif j[1] in ["7"]: # 57xxx
                                raise NotImplementedError("57xxx is not implemented yet")
#                                 self.data["cloudDirElevation"] = section3._cloud_direction_elevation(next_group)
#                                 # print("section 3 group 5 dir and elevation of cloud")
                            elif j[1] in ["8", "9"]: # 5[89]xxx
                                data["pressure_change"] = section3._PressureChange().decode(next_group)

    #                     isGroup5    = True
    #                     radDuration = None
    #                     while isGroup5: # 5xxxx
    #                         if next_group.startswith("5") and len(next_group) == 5:
    #                             j = list(next_group)
    #                             if j[1] in ["0", "1", "2", "3"]: # 5[01234]xxx
    #                                 data["evapotranspiration"] = section3._Evapotranspiration().decode(next_group)
    #                             elif j[1] in ["4"]: # 54xxx
    #                                 print("54xxx")
    #                             elif j[1] == "5": # 55xxx
    #                                 if j[2] in ["0", "1", "2", "3"]: # 55[0123]xx
    #                                     data["sunshine"] = section3._Sunshine().decode(next_group)
    #                                 elif j[2] in ["4", "5"]: # 55[45]xx
    #                                     print("55[45]xx")
    #                                 elif j[2] == "/": # 55/xx
    #                                     print("55/xx")
    # #                                     self.data["sunshine"] = section3._sunshine(next_group)
    #                                 else:
    #                                     print("bad sunshine")
    # #                                     # print("more sunshine ({})".format(next_group))
    #                             elif j[1] in ["6"]: # 56xxx
    #                                 data["cloud_drift_direction"] = section3._CloudDriftDirection().decode(next_group)
    #                             elif j[1] in ["7"]: # 57xxx
    #                                 print("57xxx")
    # #                                 self.data["cloudDirElevation"] = section3._cloud_direction_elevation(next_group)
    # #                                 # print("section 3 group 5 dir and elevation of cloud")
    #                             elif j[1] in ["8", "9"]: # 5[89]xxx
    #                                 print("58xxx")
    # #                                 self.data["pressureChange"] = section3._pressure_change(next_group)
    # #                         elif radDuration is not None:
    # #                             if re.match(r"^([012346]|5[01234])", next_group):
    # #                                 if "radiation" not in self.data:
    # #                                     self.data["radiation"] = []
    # #                                 radiation = section3._radiation(next_group)
    # #                                 radiation.duration = radDuration
    # #                                 if radDuration == "1h":
    # #                                     radiation.amount.setUnit("kJ/m2")
    # #                                 elif radDuration == "24h":
    # #                                     radiation.amount.setUnit("J/cm2")
    # #                                 radiation.convertUnit()
    # #                                 self.data["radiation"].append(radiation)
    # #                                 radDuration = None
    #                             else:
    #                                 isGroup5 = False
    #                                 i = int(next_group[0:1])
    # #                             isRadiation = None
    #                         else:
    #                             isGroup5 = False
    #                             i = int(next_group[0:1])
    #                         next_group = next(groups)
                    elif header == 6:
                        # Check that we are expecting precipitation information in section 3
                        # If not, raise error
                        try:
                            if data["precipitation_indicator"]["in_group_3"]:
                                data["precipitation_s3"] = section1._Precipitation().decode(next_group)
                        except Exception:
                            raise pymetdecoder.DecodeError("Unexpected precipitation group found in section 3")
                    elif header == 7:
                        data["precipitation_s3"] = section3._Precipitation().decode(next_group) # tenths of mm
                    elif header == 8:
                        if "cloud_layer" not in data:
                            data["cloud_layer"] = []
                        data["cloud_layer"].append(section3._CloudLayer().decode(next_group))
                    elif header == 9:
                        if next_group.startswith("9") and len(next_group) == 5:
                            j = list(next_group)
                            if j[1] == "0":
                                if j[2] == "7":
                                    # print(next_group)
                                    time_before_obs = section3._TimeBeforeObs().decode(next_group[3:5])
                                elif j[2] == "9": # 909xx
                                    data["precipitation_end"] = section3._PrecipitationEnd().decode(next_group)
                                else:
                                    raise NotImplementedError("90xxx is not implemented yet")
                            elif j[1] == "1":
                                if j[2] == "0":
                                    if "highest_gust" not in data:
                                        data["highest_gust"] = []
                                    data["highest_gust"].append(section3._HighestGust().decode(next_group,
                                        unit = data["wind_indicator"]["unit"] if data["wind_indicator"] is not None else None,
                                        measure_period = { "value": 10, "unit": "min" }
                                    ))
                                elif j[2] == "1":
                                    try:
                                        time_before = time_before_obs
                                    except Exception:
                                        time_before = def_time_before
                                    if "highest_gust" not in data:
                                        data["highest_gust"] = []
                                    data["highest_gust"].append(section3._HighestGust().decode(next_group,
                                        unit = data["wind_indicator"]["unit"] if data["wind_indicator"] is not None else None,
                                        time_before = time_before
                                    ))
                                elif j[2] in ["2", "3", "4"]:
                                    try:
                                        time_before = time_before_obs
                                    except Exception:
                                        time_before = def_time_before
                                    if "mean_wind" not in data:
                                        data["mean_wind"] = { "time_before": time_before }
                                    attrs = [None, None, "highest", "mean", "lowest"]
                                    data["mean_wind"][attrs[int(j[2])]] = section3._MeanWind().decode(next_group[3:5],
                                        unit = data["wind_indicator"]["unit"] if data["wind_indicator"] is not None else None,
                                        # time_before = time_before
                                    )
                                else:
                                    print(next_group)
                            elif j[1] == "2":
                                raise NotImplementedError("92xxx is not implemented yet")
                            elif j[1] == "3":
                                raise NotImplementedError("93xxx is not implemented yet")
                            elif j[1] == "4":
                                raise NotImplementedError("94xxx is not implemented yet")
                            elif j[1] == "5":
                                raise NotImplementedError("95xxx is not implemented yet")
                            elif j[1] == "6":
                                raise NotImplementedError("96xxx is not implemented yet")
                            elif j[1] == "7":
                                raise NotImplementedError("97xxx is not implemented yet")
                            elif j[1] == "8":
                                raise NotImplementedError("98xxx is not implemented yet")
                            elif j[1] == "9":
                                raise NotImplementedError("99xxx is not implemented yet")
                        # print(next_group)

                    next_group = next(groups)

            ### SECTION 4 ###
            if next_group == "444":
                next_group = next(groups)
                last_header = None
                logging.warning("444 not implemented yet")
                while True:
                    if re.match("^(555)$", next_group):
                        break
                    next_group = next(groups)

            ### SECTION 5 ###
            if next_group == "555":
                next_group = next(groups)
                last_header = None
                while True:
                    header = int(next_group[0])
                    if last_header is not None and header < last_header:
                        break
                    if "section5" not in data:
                        data["section5"] = []
                    data["section5"].append(next_group)
                    next_group = next(groups)


                # # Parse the next group, based on the group header
                # for i in range(0, 10):
                #     try:
                #         if not re.match("^(555)$", next_group):
                #             header = int(next_group[0:1])
                #         else:
                #             header = None
                #     except ValueError as e:
                #         logging.warning("{} is not a valid section 3 group".format(next_group))
                #         break
                #
                #     # need to deal with multiple 5-groups and 8-groups. if there are more than
                #     # 10 groups in 333, then it doesn't work
                #     if header <= i:
                #         print(next_group)
                        # next_group = next(groups)

        #         for i in range(0, 10):
        #             try:
        #                 if not re.match("^(555)$", next_group):
        #                     header = int(next_group[0:1])
        #                 else:
        #                     header = None
        #             except ValueError as e:
        #                 logging.warning("{} is not a valid section 3 group".format(next_group))
        #                 break
        #             if header == i:
        #                 if i == 0:
        #                     logging.warning("section 3 group 0")
        #                 if i == 1:
        #                     if not self._isGroupValid(next_group):
        #                         logging.warning("{} is an invalid maximum temperature group".format(next_group))
        #                         next_group = next(groups)
        #                         continue
        #                     self.data["maximumTemperature"] = section1._temperature(next_group)
        #                 if i == 2:
        #                     if not self._isGroupValid(next_group):
        #                         logging.warning("{} is an invalid minimum temperature group".format(next_group))
        #                         next_group = next(groups)
        #                         continue
        #                     self.data["minimumTemperature"] = section1._temperature(next_group)
        #                 if i == 3:
        #                     if not self._isGroupValid(next_group):
        #                         logging.warning("{} is an invalid ground state group".format(next_group))
        #                         next_group = next(groups)
        #                         continue
        #                     if not self.data["region"].value in ["II", "III", "IV", "VI"]:
        #                         logging.warning("Ground state not measured in region {}".format(self.data["region"].value))
        #                         next_group = next(groups)
        #                         continue
        #                     self.data["groundState"] = section3._ground_state(next_group)
        #
        #                     # Temperatures are not included in Region IV
        #                     if self.data["region"].value == "IV" and self.data["groundState"].temperature.available:
        #                         logging.warning("Ground temperature found, but it is not included in Region IV")
        #                         self.data["groundState"].temperature.available = False
        #                         delattr(self.data["groundState"].temperature, "value")
        #                 if i == 4:
        #                     if not self._isGroupValid(next_group):
        #                         logging.warning("{} is an invalid solid precipitation group".format(next_group))
        #                         next_group = next(groups)
        #                         continue
        #                     self.data["groundStateSnow"] = section3._ground_state_snow(next_group)
        #                 if i == 5:
        #                     isGroup5    = True
        #                     radDuration = None
        #                     while isGroup5: # 5xxxx
        #                         if next_group.startswith("5") and len(next_group) == 5:
        #                             j = list(next_group)
        #                             if j[1] in ["0", "1", "2", "3"]: # 5[01234]xxx
        #                                 self.data["evapotranspiration"] = section3._evapotranspiration(next_group)
        #                             elif j[1] in ["4"]: # 54xxx
        #                                 print("section 3 group 5 temperature change")
        #                             elif j[1] == "5": # 55xxx
        #                                 if j[2] in ["0", "1", "2"]: # 55[012]xx
        #                                     self.data["sunshine"] = section3._sunshine(next_group)
        #                                     radDuration = "24h"
        #                                 elif j[2] == "3":
        #                                     self.data["sunshine"] = section3._sunshine(next_group)
        #                                     radDuration = "1h"
        #                                     # print("sunshine over previous hour. also radiation ({})".format(next_group))
        #                                 elif j[2] in ["4", "5"]: # 55[45]xx
        #                                     print("radiation")
        #                                 elif j[2] == "/": # 55/xx
        #                                     self.data["sunshine"] = section3._sunshine(next_group)
        #                                 else:
        #                                     print("bad sunshine")
        #                                     # print("more sunshine ({})".format(next_group))
        #                             elif j[1] in ["6"]: # 56xxx
        #                                 self.data["cloudDriftDirection"] = section3._cloud_drift_direction(next_group)
        #                             elif j[1] in ["7"]: # 57xxx
        #                                 self.data["cloudDirElevation"] = section3._cloud_direction_elevation(next_group)
        #                                 # print("section 3 group 5 dir and elevation of cloud")
        #                             elif j[1] in ["8", "9"]: # 5[89]xxx
        #                                 self.data["pressureChange"] = section3._pressure_change(next_group)
        #                         elif radDuration is not None:
        #                             if re.match(r"^([012346]|5[01234])", next_group):
        #                                 if "radiation" not in self.data:
        #                                     self.data["radiation"] = []
        #                                 radiation = section3._radiation(next_group)
        #                                 radiation.duration = radDuration
        #                                 if radDuration == "1h":
        #                                     radiation.amount.setUnit("kJ/m2")
        #                                 elif radDuration == "24h":
        #                                     radiation.amount.setUnit("J/cm2")
        #                                 radiation.convertUnit()
        #                                 self.data["radiation"].append(radiation)
        #                                 radDuration = None
        #                             else:
        #                                 isGroup5 = False
        #                                 i = int(next_group[0:1])
        #                             isRadiation = None
        #                         else:
        #                             isGroup5 = False
        #                             i = int(next_group[0:1])
        #                         next_group = next(groups)
        #
        #                     # # Go through each group 5 code and parse accordingly
        #                     # # based on code table 2061
        #                     # for g in group5:
        #                     #     j = list(g)
        #                     #     if j[1] in ["0", "1", "2", "3"]:
        #                     #         self.data["evapotranspiration"] = section3.Evapotranspiration(g)
        #                     #     elif j[1] in ["4"]:
        #                     #         print("section 3 group 5 temperature change")
        #                     #     elif j[1] == "5":
        #                     #         print("section 3 group 5 sunshine ({})".format(g))
        #                     #         if j[2] in ["0", "1", "2"]:
        #                     #             self.data["sunshine"] = section3.Sunshine(g)
        #                     #         elif j[2] == "3":
        #                     #             self.data["sunshine"] = section3.Sunshine(g)
        #                     #             # self.data[]
        #                     #             print("sunshine over previous hour. also radiation ({})".format(next_group))
        #                     #         elif j[2] in ["4", "5"]:
        #                     #             print("radiation")
        #                     #         elif j[2] == "/":
        #                     #             print("cant do sunshine")
        #                     #         else:
        #                     #             print("bad sunshine")
        #                     #             # print("more sunshine ({})".format(next_group))
        #                     #     elif j[1] in ["6"]:
        #                     #         print("section 3 group 5 cloud drift")
        #                     #     elif j[1] in ["7"]:
        #                     #         print("section 3 group 5 dir and elevation of cloud")
        #                     #     elif j[1] in ["8", "9"]:
        #                     #         print("section 3 group 5 surface pressure change")
        #                 if i == 6:
        #                     logging.warning("section 3 group 6")
        #                 if i == 7:
        #                     logging.warning("section 3 group 7")
        #                 if i == 8:
        #                     logging.warning("section 3 group 8")
        #                 if i == 9:
        #                     logging.warning("section 3 group 9")
        #                 next_group = next(groups)
        except StopIteration:
            # If we have reached this point with iceGroups still intact, parse them
            try:
                # pass
                if len(ice_groups) > 0:
                    data["sea_land_ice"] = section2._SeaLandIce().decode(ice_groups)
            except UnboundLocalError as e:
                pass
            return data

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
            ("station_type", section0._StationType, {}),
            ("callsign", section0._Callsign, {}),
            [("obs_time", section0._ObservationTime, {}), ("wind_indicator", section0._WindIndicator, {})],
            ("station_id", section0._StationID, {}),
            ("station_position", section0._StationPosition, { "obs_type": data["station_type"]["value"] })
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
                    ("precipitation_indicator", section1._PrecipitationIndicator, {}, True),
                    ("weather_indicator", section1._WeatherIndicator, {}, True),
                    ("lowest_cloud_base", section1._LowestCloudBase, {}, True),
                    ("visibility", section1._Visibility, { "use90": useVis90 }, True)
                ],[
                    ("cloud_cover", section1._CloudCover, { "allow_none": True }, True),
                    ("surface_wind", section1._SurfaceWind, {}, True)
                ],
                ("air_temperature", section1._Temperature, { "group": "1" }, False),
                ("dewpoint_temperature", section1._Temperature, { "group": "2" }, False),
                ("relative_humidity", section1._RelativeHumidity, { "group": "29" }, False),
                ("station_pressure", section1._Pressure, { "group": "3" }, False),
                ("sea_level_pressure", section1._Pressure, { "group": "4" }, False),
                ("geopotential", section1._Geopotential, { "group": "4" }, False),
                ("pressure_tendency", section1._PressureTendency, { "group": "5" }, False),
                ("precipitation_s1", section1._Precipitation, { "group": "6" }, False),
                [
                    ("present_weather", section1._Weather, { "group": "7", "weather_type": "present" }, False),
                    ("past_weather", section1._Weather, { "weather_type": "past" }, False)
                ],
                ("cloud_types", section1._CloudType, { "group": "8" }, False),
                ("exact_obs_time", section1._ExactObservationTime, { "group": "9" }, False)
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
            groups.append(section2._ShipDisplacement().encode(data["displacement"], group="222", allow_none=True))
            has_section_2 = True

        # Only encode rest of section 2 if required
        if has_section_2:
            _section2 = [
                ("sea_surface_temperature", section2._SeaSurfaceTemperature, { "group": "0" }, False),
                ("wind_waves", section2._WindWaves, { "_group": "1" }, False),
                ("wind_waves", section2._WindWaves, { "_group": "2" }, False),
                ("swell_waves", section2._SwellWaves, {}, False),
                ("ice_accretion", section2._IceAccretion, { "group": "6" }, False),
                ("wind_waves", section2._WindWaves, { "_group": "7" }, False),
                ("wet_bulb_temperature", section2._WetBulbTemperature, { "group": "8" }, False),
                ("sea_land_ice", section2._SeaLandIce, {}, False)
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
        _section3 = [
            ("maximum_temperature", section1._Temperature, { "group": "1" }, False),
            ("minimum_temperature", section1._Temperature, { "group": "2" }, False),
            ("ground_state", section3._GroundState, { "group": "3" }, False),
            ("ground_state_snow", section3._GroundStateSnow, { "group": "4" }, False),
            ("evapotranspiration", section3._Evapotranspiration, { "group": "5" }, False),
            ("sunshine", section3._Sunshine, { "group": "55" }, False),
            ("cloud_drift_direction", section3._CloudDriftDirection, { "group": "56" }, False),
            ("pressure_change", section3._PressureChange, { "group": "5" }, False),
            ("precipitation_s3", section3._Precipitation, { }, False),
            ("cloud_layer", section3._CloudLayer, { "use90": useCloud90 }, False),
            ("precipitation_end", section3._PrecipitationEnd, {}, False),
            ("highest_gust", section3._HighestGust, { "time_before": weather_time }, False),
            ("mean_wind", section3._MeanWind, { "time_before": weather_time }, False)
        ]
        for s in _section3:
            if isinstance(s, tuple):
                s = [s]
            group = []
            for x in s:
                if x[0] in data:
                    if data[x[0]] is None:
                        val = None
                    val = data[x[0]]
                    obj = x[1]
                    attrs = x[2]
                    if x[0] == "precipitation_s3":
                        if "time_before_obs" in val and val["time_before_obs"] == { "value": 24, "unit": "h" }:
                            obj = section3._Precipitation
                        else:
                            obj = section1._Precipitation
                            attrs = { "group": "6" }
                    group.append(obj().encode(val, **attrs))
                else:
                    if x[3]:
                        raise pymetdecoder.EncodeError("Required variable '{}' is missing".format(x[0]))
                        return None
            if len(group) > 0:
                s3_groups.append("".join(group))
        if len(s3_groups) > 0:
            groups.extend(["333"] + s3_groups)

        ### SECTION 5
        if "section5" in data:
            groups.extend(["555"] + data["section5"])

        # Return the encoded report
        return " ".join(groups)

        # if "station_type" in data:
            # groups.append(section0._StationType().encode(data["station_type"]))
        # try:
        #     groups = []
        #     parsed = ["region"] # pre-populate with stuff we don't need to re-encode
        #     # if "station_type" in data:
        #     #     groups.append(section0._StationType().encode(data["station_type"]))
        #     groups.append(section0._StationType().encode(data["station_type"] if "station_type" in data else {}))
        #     parsed.append("station_type")
        #     if "callsign" in data:
        #         if "value" in data["callsign"]:
        #             groups.append(section0._Callsign().encode(data["callsign"]["value"]))
        #             parsed.append("callsign")
        #     obs_time = section0._ObservationTime().encode(data["obs_time"] if "obs_time" in data else {})
        #     wind_ind = section0._WindIndicator().encode(data["wind_indicator"] if "wind_indicator" in data else {})
        #     groups.append("{}{}".format(obs_time, wind_ind))
        #     parsed.extend(("obs_time", "wind_indicator"))
        #     if "station_id" in data:
        #         groups.append(section0._StationID().encode(data["station_id"] if "station_id" in data else {}))
        #         parsed.append("station_id")
        #     if "station_position" in data:
        #         groups.append(
        #             section0._StationPosition().encode(
        #                 data["station_position"] if "station_position" in data else {},
        #                 obs_type = data["station_type"])
        #             )
        #         parsed.append("station_position")
        #     precip_ind  = section1._PrecipitationIndicator().encode(data["precipitation_indicator"] if "precipitation_indicator" in data else {})
        #     weather_ind = section1._WeatherIndicator().encode(data["weather_indicator"] if "weather_indicator" in data else {})
        #     cloud_base  = section1._LowestCloudBase().encode(data["lowest_cloud_base"] if "lowest_cloud_base" in data else {})
        #     visibility  = section1._Visibility().encode(data["visibility"] if "visibility" in data else {})
        #     groups.append("{}{}{}{}".format(precip_ind, weather_ind, cloud_base, visibility))
        #     parsed.extend(("precipitation_indicator", "weather_indicator", "lowest_cloud_base", "visibility"))
        #     cloud_cover = section1._CloudCover().encode(data["cloud_cover"] if "cloud_cover" in data else {})
        #     surface_wind = section1._SurfaceWind().encode(data["surface_wind"] if "surface_wind" in data else {})
        #     groups.append("{}{}".format(cloud_cover, surface_wind))
        #     parsed.extend(("cloud_cover", "surface_wind"))
        #     if "air_temperature" in data:
        #         groups.append(section1._Temperature().encode(data["air_temperature"], group="1"))
        #         parsed.append("air_temperature")
        #     if "dewpoint_temperature" in data:
        #         groups.append(section1._Temperature().encode(data["dewpoint_temperature"], group="2"))
        #         parsed.append("dewpoint_temperature")
        #     if "relative_humidity" in data:
        #         groups.append(section1._RelativeHumidity().encode(data["relative_humidity"]))
        #         parsed.append("relative_humidity")
        #     if "station_pressure" in data:
        #         groups.append(section1._Pressure().encode(data["station_pressure"], group="3"))
        #         parsed.append("station_pressure")
        #     if "sea_level_pressure" in data:
        #         groups.append(section1._Pressure().encode(data["sea_level_pressure"], group="4"))
        #         parsed.append("sea_level_pressure")
        #     if "geopotential" in data:
        #         groups.append(section1._Geopotential().encode(data["geopotential"]))
        #         parsed.append("geopotential")
        #     if "pressure_tendency" in data:
        #         groups.append(section1._PressureTendency().encode(data["pressure_tendency"]))
        #         parsed.append("pressure_tendency")
        #     if "precipitation" in data:
        #         groups.append(section1._Precipitation().encode(data["precipitation"]))
        #         parsed.append("precipitation")
        #     if "present_weather" in data or "past_weather" in data:
        #         # groups.append(section1._Weather().encode(data["present_weather"]))
        #         if "present_weather" in data:
        #             present_weather = section1._Weather().encode(data["present_weather"], weather_type="present")
        #         if "past_weather" in data:
        #             past_weather = [
        #                 section1._Weather().encode(data["past_weather"][0], weather_type="past"),
        #                 section1._Weather().encode(data["past_weather"][1], weather_type="past"),
        #             ]
        #         groups.append("7{}{}".format(present_weather, "".join(past_weather)))
        #         parsed.extend(("present_weather", "past_weather"))
        #     if "cloud_types" in data:
        #         groups.append(section1._CloudType().encode(data["cloud_types"]))
        #         parsed.append("cloud_types")
        #     if "exact_obs_time" in data:
        #         groups.append(section1._ExactObservationTime().encode(data["exact_obs_time"]))
        #         parsed.append("exact_obs_time")
        # except Exception as e:
        #     logging.error("Error when encoding: {}".format(str(e)))
        #     sys.exit(1)
        #
        # # Check if everything was parsed
        # for d in data.keys():
        #     if d not in parsed:
        #         raise pymetdecoder.DecodeError("Unable to encode parameter '{}'".format(d))

        # # Return the encoded report
        # return " ".join(groups)

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
                if not self._isGroupValid(next_group):
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

    def _parseYYGGi(self, group): # YYGGi
        """
        Parses the observation time and wind indicator group (YYGGi) and sets
        the obsTime and windIndicator data values

        :param string group: SYNOP code to decode
        """
        # Check group matches regular expression
        if not self._isGroupValid(group):
            raise pymetdecoder.DecodeError("{} is an invalid YYGGi group".format(group))
            return

        # Get observation time and wind indicator
        return (
            section0._ObservationTime().decode(group[0:4]),
            section0._WindIndicator().decode(group[4])
        )
    def _parseiihVV(self, group): # iihVV
        """
        Parses the precipitation and weather indicator and cloud base group (iihVV)
        and sets the precipitationIndicator, weatherIndicator and lowestCloudBase
        data values

        :param string group: SYNOP code to decode
        """
        # Check group matches regular expression
        if not self._isGroupValid(group):
            logging.warning("{} is an invalid iihVV group".format(group))
            return

        # Get precipitation, weather, lowest cloud and horizontal visibilty
        return (
            section1._PrecipitationIndicator().decode(group[0:1]),
            section1._WeatherIndicator().decode(group[1:2]),
            section1._LowestCloudBase().decode(group[2:3]),
            section1._Visibility().decode(group[3:5])
        )
    def _parseNddff(self, group, unit=None): # Nddff
        """
        Parses the cloud cover and surface wind group (Nddff) and sets the cloudCover
        and surfaceWind data values

        :param string group: SYNOP code to decode
        """
        if not self._isGroupValid(group):
            logging.warning("{} is an invalid Nddff group".format(group))
            return

        # Get cloud cover, wind direction and speed
        cloud_cover  = section1._CloudCover().decode(group[0:1])
        surface_wind = section1._SurfaceWind().decode(group[1:5])
        if surface_wind is not None and surface_wind["speed"] is not None:
            surface_wind["speed"]["unit"] = unit
        return (cloud_cover, surface_wind)

        # # Get total cloud cover (N)
        # self.data["cloudCover"] = section1._cloud_cover(group[0:1])
        #
        # # Get wind direction (dd) and wind speed (ff)
        # self.data["surfaceWind"] = section1._surface_wind(group[1:5])
        # if hasattr(self.data["surfaceWind"], "speed") and hasattr(self.data["windIndicator"], "unit"):
        #     self.data["surfaceWind"].speed.setUnit(self.data["windIndicator"].unit)
    def _parse_s1_weather(self, group, data): # 7wwWW
        if "weather_indicator" in data:
            try:
                if data["weather_indicator"]["value"] not in [1, 4, 7]:
                    logging.warning("Group 7 codes found, despite reported as being omitted (ix = {})".format(data["weather_indicator"]["value"]))
            except AttributeError:
                pass

            present_weather = section1._Weather().decode(group[1:3])
            past_weather = [
                section1._Weather().decode(group[3:4]),
                section1._Weather().decode(group[4:5])
            ]
            return (present_weather, past_weather)
    def parseAirTemperature(self, group): # 1snTTT
        """
        Parses the air temperature group (1snTTT) and sets the air temperature
        data value

        :param string group: SYNOP code to decode
        """
        if not self._isGroupValid(group):
            raise pymetdecoder.DecodeError("{} is an invalid air temperature group".format(group))

        # Prepare the data
        if "temperature" not in self.data:
            self.data["temperature"] = {}
        self.data["temperature"]["air"] = section1._temperature(group)
    def parseDewpointHumidity(self, group): # 2snTTT or 29UUU
        """
        Parses the dewpoint temperature/relative humidity group (2snTTT or 29UUU)
        and sets the relativeHumidity and/or dewpoint temperature data values

        :param string group: SYNOP code to decode
        """
        if not self._isGroupValid(group):
            logging.warning("{} is an invalid dewpoint temperature/relative humidity group".format(group))
            return

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
            self.data["temperature"]["dewpoint"] = section1._temperature(group)
    def parseSeaLevelPressureGeopotential(self, group): # 4PPPP or 4ahhh
        """
        Parses the sea level pressure/geopotential group (4PPPP or 4ahhh) and sets
        the seaLevelPressure and/or geopotential data values

        :param string group: SYNOP code to decode
        """
        if not self._isGroupValid(group):
            logging.warning("{} is an invalid sea level pressure/geopotential group".format(group))
            return

        # Determine if this is pressure or geopotential height
        a = group[1]
        if a in ["0", "9"]:
            self.data["seaLevelPressure"] = section1._pressure(group)
        elif a in ["1", "2", "5", "7", "8", "/"]:
            self.data["geopotential"] = section1._geopotential(group)
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
