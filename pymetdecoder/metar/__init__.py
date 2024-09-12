################################################################################
# pymetdecoder/metar/__init__.py
#
# METAR decoder module for pymetdecoder
#
# TDBA 2024-09-06:
#   * First version
################################################################################
# CONFIGURATION
################################################################################
import re, pymetdecoder
from . import observations as obs

# Define the sections
# Tuple: (keyword, obs_class, is_array)
SECTIONS =  [
    ("is_special", obs.IsSpecial, False),
    ("is_corrected", obs.IsCorrected, False),
    ("callsign", obs.Callsign, False),
    ("obs_time", obs.ObservationTime, False),
    ("is_automatic", obs.IsAutomatic, False),
    ("surface_wind", obs.SurfaceWind, False),
    ("cavok", None, False),
    ("prevailing_visibility", obs.Visibility, False),
    ("visibility_variation", obs.Visibility, False),
    ("runway_visual_range", obs.RunwayVisual, True),
    ("present_weather", obs.PresentWeather, True),
    ("cloud_types", obs.CloudAmountHeight, True),
    ("vertical_visibility", obs.VerticalVisibility, False),
    ("temperature", obs.Temperature, False),
    ("qnh", obs.QNH, False),
    ("recent_weather", obs.RecentWeather, False),
    ("trend", obs.Trend, False),
    ("remarks", obs.Remarks, False)
]
################################################################################
# REPORT CLASSES
################################################################################
class METAR(pymetdecoder.Report):
    def _decode(self, message):
        """
        Decodes the METAR and sets the data attribute with the information
        """
        # Initialise groups to parse
        parse_groups = {}
        
        # Create iterator of the message components
        groups = iter(message.split())

        # Go through the groups
        data = {}
        try:
            # Determine if observation is METAR or SPECI
            parse_groups["is_special"] = next(groups)

            # Get callsign. The COR (corrected) keyword can appear here
            grp = next(groups)
            if grp == "COR":
                parse_groups["is_corrected"] = grp
                grp = next(groups)
            # else:
            #     data["is_corrected"] = obs.IsCorrected().decode(" ")
            parse_groups["callsign"] = grp

            # Determine date/time of observation
            YYGGgg = next(groups)
            parse_groups["obs_time"] = YYGGgg

            # If this section ends with NIL, that's the end of the METAR
            # Sometimes COR can appear here too, so check again
            grp = next(groups)
            if grp == "NIL":
                raise StopIteration
            if grp == "COR" and "is_corrected" not in parse_groups:
                parse_groups["is_corrected"] = grp
                grp = next(groups)
            # else:
            #     parse_groups["is_corrected"] = " "

            # If the next group is AUTO, then this report is fully automatic
            # auto = obs.IsAutomatic()
            if grp == "AUTO":
                parse_groups["is_automatic"] = "AUTO"
                grp = next(groups)
            else:
                parse_groups["is_automatic"] = " "

            # Determine surface wind
            sw_groups = [grp]
            grp = next(groups)
            if re.match(obs.RE_SURFACE_WIND, grp):
                sw_groups.append(grp)
                grp = next(groups)
            parse_groups["surface_wind"] = sw_groups

            # Determine visibility
            vis_groups = []
            if grp == "CAVOK":
                # this has data going into visiblity, clouds and weather, so
                # will have to deal with this slightly differently
                # for now, just set CAVOK to true
                parse_groups["cavok"] = True
                grp = next(groups)
            else:
                while True:
                    if re.match(r"^[0-9R]", grp):
                        vis_groups.append(grp)
                        grp = next(groups)
                    else:
                        break
                    # vis_groups.append(grp)
                    # grp = next(groups)
                    # if not re.match(r"^R\d{2}", grp):
                    #     break
            for v in vis_groups:
                if re.match(r"^R\d{2}", v):
                    if "runway_visual_range" not in parse_groups:
                        parse_groups["runway_visual_range"] = []
                    parse_groups["runway_visual_range"].append(v)
                else:
                    if "prevailing_visibility" in parse_groups:
                        parse_groups["visibility_variation"] = v
                    else:
                        parse_groups["prevailing_visibility"] = v

            # Determine present weather
            parse_groups["present_weather"] = []
            while True:
                if re.match(obs.RE_PRESENT_WEATHER, grp):
                    parse_groups["present_weather"].append(grp)
                    grp = next(groups)
                else:
                    break

            # Determine clouds
            parse_groups["cloud_types"] = []
            while True:
                if re.match(r"^[A-Z]{3}", grp):
                    parse_groups["cloud_types"].append(grp)
                    grp = next(groups)
                else:
                    break

            # Determine vertical visibility
            if re.match(r"^VV(\d{3})$", grp):
                parse_groups["vertical_visibility"] = grp[2:]
                grp = next(groups)

            # Determine temperature
            # if re.match(r"(M)?(\d){2}", grp):
            if re.match(r"^(M)?(\d{2}|\/\/)\/(M)?(\d{2}|\/\/)", grp):
                parse_groups["temperature"] = grp
                grp = next(groups)

            # Determine QNH
            if re.match(r"^[AQ][0-9]{4}$", grp):
                parse_groups["qnh"] = grp
                grp = next(groups)

            # Determine recent weather
            if grp.startswith("RE"):
                parse_groups["recent_weather"] = grp[2:]
                grp = next(groups)

            # Trends
            if grp in ["NOSIG"]:
                parse_groups["trend"] = [grp]
                grp = next(groups)
            elif grp in ["TEMPO", "BECMG"]:
                parse_groups["trend"] = [grp]
                grp = next(groups)
                while True:
                    if grp == "RMK":
                        break
                    parse_groups["trend"].append(grp)
                    grp = next(groups)

            # Remarks
            if grp == "RMK":
                parse_groups["remarks"] = []
                grp = next(groups)
                while True:
                    parse_groups["remarks"].append(grp)
                    grp = next(groups)

            # Remaining groups
            parse_groups["_unhandled"] = []
            while True:
                parse_groups["_unhandled"].append(grp)
                grp = next(groups)
            
            # If we have reached this point, stop iterating
            raise StopIteration
        except StopIteration:
            # Process each section
            for s in SECTIONS:
                if s[0] in parse_groups:
                    if s[1] is None:
                        data[s[0]] = parse_groups[s[0]]
                        continue
                    if s[2]:
                        if not isinstance(parse_groups[s[0]], list):
                            parse_groups[s[0]] = [parse_groups[s[0]]]
                        if len(parse_groups[s[0]]) == 0:
                            continue
                        data[s[0]] = []
                        for d in parse_groups[s[0]]:
                            data[s[0]].append(s[1]().decode(d))
                    else:
                        data[s[0]] = s[1]().decode(parse_groups[s[0]])
        except UnboundLocalError as e:
            # import traceback
            # traceback.print_exc()
            print("error found: {}".format(str(e)))            

        # Return the data
        return data
        
    def _encode(self, data, **kwargs):
        """
        Encodes the METAR from data
        """
        # Initialise groups
        groups = []

        # Process each section
        for s in SECTIONS:
            if s[0] == "cavok" and "cavok" in data:
                groups.append("CAVOK")
                continue
            if s[0] in data:
                group = s[1]().encode(data[s[0]])
                if group is not None:
                    groups.append(group)

        # Return the encoded report
        return " ".join(groups)


