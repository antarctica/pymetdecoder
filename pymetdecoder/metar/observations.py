################################################################################
# pymetdecoder/metar/observations.py
#
# Observation classes from METAR
#
# TDBA 2024-09-06:
#   * First version
################################################################################
# CONFIGURATION
################################################################################
import re, math
from fractions import Fraction
from pymetdecoder import Observation, logging, DecodeError, EncodeError, InvalidCode
from pymetdecoder import code_tables as ct

# Define common regular expressions here
RE_PRESENT_WEATHER = r"^(NSW|[\+\-]?([A-Z]{2}))+$"
RE_SURFACE_WIND = r"^(\d){3}V(\d){3}$"
RE_TEMPERATURE = r"^(M)?(\d{2}|\/\/)\/(M)?(\d{2}|\/\/)$"
################################################################################
# SHARED CLASSES
################################################################################
class Day(Observation):
    """
    Day of observation
    """
    _CODE_LEN = 2
    _VALID_RANGE = (1, 31)
class DirectionDegrees(Observation):
    """
    Direction in degrees
    """
    _CODE_LEN = 3
    _UNIT = "deg"
    _VALID_RANGE = (0, 360)
class Hour(Observation):
    """
    Hour of observation
    """
    _CODE_LEN = 2
    _VALID_RANGE = (0, 24)
class Minute(Observation):
    """
    Minute of observation
    """
    _CODE_LEN = 2
    _VALID_RANGE = (0, 59)
################################################################################
# OTHER CLASSES
################################################################################
class Callsign(Observation):
    """
    Callsign

    * CCCC - ICAO identifier of the reporting station
    """
    def _decode(self, callsign):
        return { "value": str(callsign).upper() }
    def _encode(self, data):
        return str(data["value"]).upper()
class CloudAmountHeight(Observation):
    """
    Cloud amount and height

    * NNN - cloud amount
    * hhh - cloud height
    """
    _CODE_LEN = 6
    def _decode(self, cloud):
        try:
            (NNN, hhh, convective) = re.match(r"^([A-Z]{3})([0-9]*)(CB|TCU|\/\/\/)?$", cloud).groups()
        except: 
            raise InvalidCode(cloud, "cloud amount and height")
        return {
            "amount": self.Amount().decode(NNN),
            "height": self.Height().decode(hhh) if NNN not in ["NSC", "NCD"] else None,
            "convective": self.Convective().decode(convective)
        }
    def _encode(self, data):
        clouds = []
        for d in data:
            NNN = self.Amount().encode(d["amount"] if "amount" in d else None, allow_none=True)
            if NNN not in ["NSC", "NCD", "SKC", "CLR"]:
                hhh = self.Height().encode(d["height"] if "height" in d else None, allow_none=True)
                clouds.append("{NNN}{hhh}{cu}".format(
                    NNN = NNN,
                    hhh = hhh,
                    cu  = self.Convective().encode(d["convective"] if "convective" in d else None, allow_none=True)
                ))
            else:
                clouds.append(NNN)
        return " ".join(clouds)
    class Amount(Observation):
        """
        Cloud amount
        """
        _VALID_VALUES = ["NSC", "NCD", "CLR", "SKC", "FEW", "SCT", "BKN", "OVC"]
        _VALID_RANGE = (0, 8)
        def _decode(self, NNN):
            if NNN == "NSC":
                return { "value": None, "clouds_detected": True }
            elif NNN == "NCD":
                return { "value": None, "clouds_detected": False }
            elif NNN == "CLR":
                return { "value": 0, "unit": "okta", "clouds_detected": False  }
            elif NNN == "SKC":
                return { "value": 0, "unit": "okta", "clouds_detected": True  }
            elif NNN == "FEW":
                return { "value": NNN, "min": 1, "max": 2, "unit": "okta", "clouds_detected": True  }
            elif NNN == "SCT":
                return { "value": NNN, "min": 3, "max": 4, "unit": "okta", "clouds_detected": True  }
            elif NNN == "BKN":
                return { "value": NNN, "min": 5, "max": 7, "unit": "okta", "clouds_detected": True  }
            elif NNN == "OVC":
                return { "value": 8, "unit": "okta" }
            else:
                raise InvalidCode(NNN, "cloud amount")
        def _encode(self, data, **kwargs):
            if "clouds_detected" in data:
                detected = data["clouds_detected"]
            else:
                detected = False if data["value"] is None else True

            if data["value"] is None:
                return "NSC" if detected else "NCD"

            if isinstance(data["value"], int):
                if data["value"] == 0:
                    return "SKC" if detected else "CLR"
                elif 1 <= data["value"] <= 2:
                    return "FEW"
                elif 3 <= data["value"] <= 4:
                    return "SCT"
                elif 5 <= data["value"] <= 7:
                    return "BKN"
                else:
                    return "OVC"
            else:
                # if data["value"] in ["FEW", "SCT", "BKN", "OVC"]:
                return data["value"]
    class Height(Observation):
        _CODE_LEN = 3
        _CODE_TABLE = ct.CodeTable1690
        _UNIT = "m"
    class Convective(Observation):
        def is_available(self, value):
            return True
        def _decode(self, cu):
            return {
                "cumulonimbus": True if cu == "CB" else False,
                "towering_cumulus": True if cu == "TCU" else False,
                "not_observable": True if cu == "///" else False
            }
        def _encode(self, data, **kwargs):
            if data is None:
                return ""
            if "cumulonimbus" in data and data["cumulonimbus"]:
                return "CB"
            elif "towering_cumulus" in data and data["towering_cumulus"]:
                return "TCU"
            elif "not_observable" in data and data["not_observable"]:
                return "///"
            else:
                return ""
class IsAutomatic(Observation):
    """
    Is this an automatic (AUTO) obs?

    * ob_type - AUTO if automatic, blank otherwise
    """
    def _decode(self, ob_type):
        if ob_type == " ":
            return False
        elif ob_type == "AUTO":
            return True
        else:
            raise DecodeError("Cannot determine if report is automatic from {}".format(ob_type))
    def _encode(self, data):
        return "AUTO" if data else None
class IsCAVOK(Observation):
    """
    CAVOK (Cloud And Visibility OK)
    """
    _ENCODE_DEFAULT = None
    def _decode(self, cavok):
        return True if cavok == "CAVOK" else False
    def _encode(self, cavok, data={}):
        # If we already have a boolean for CAVOK (i.e. it's been calculated elsewhere
        # or obtained from a decoded METAR), then do not calculate.
        if isinstance(cavok, bool):
            return "CAVOK" if cavok else None

        # Determine CAVOK by looking at other observations
        try:
            # Visibility must be >= 10km. If not, no CAVOK
            if data["prevailing_visibility"]["value"] < 10000:
                return None

            # No visibility variation (VVVVD) is allowed
            if "visibility_variation" in data:
                return None

            # No clouds below 1500m (5000 ft) and no convective clouds
            for c in data["cloud_types"]:
                if c["height"] is not None and c["height"]["value"] < 1500:
                    return None
                if any([k for k in c["convective"].values()]):
                    return None

            # No significant weather
            for w in data["present_weather"]:
                if not w["no_significant_weather"] or "no_significant_weather" not in w:
                    return None
        except KeyError:
            return None

        # If we have reached this point, we have CAVOK
        return "CAVOK"
class IsCorrected(Observation):
    """
    Is this a corrected (COR) obs?

    * corrected - COR if corrected, blank otherwise
    """
    def _decode(self, ob_type):
        if ob_type == " ":
            return False
        elif ob_type == "COR":
            return True
        else:
            raise DecodeError("Cannot determine if report is corrected from {}".format(ob_type))
    def _encode(self, data):
        return "COR" if data else None
class IsSpecial(Observation):
    """
    Is this a SPECI obs?

    * ob_type - message type (either METAR or SPECI) 
    """
    _DESCRIPTION = "message type"
    _VALID_REGEXP = "^(METAR|SPECI)"
    def _decode(self, ob_type):
        if self.is_valid(ob_type):
            if ob_type == "METAR":
                return False
            elif ob_type == "SPECI":
                return True
            else:
                raise DecodeError("Report is not a METAR or SPECI")
    def _encode(self, data):
        if data:
            return "SPECI"
        else:
            return "METAR"
class ObservationTime(Observation):
    """
    Observation time
    """
    _CODE_LEN = 7
    _COMPONENTS = [
        ("day", 0, 2, Day),
        ("hour", 2, 2, Hour),
        ("minute", 4, 2, Minute)
    ]
    def _decode(self, dt):
        if not dt.endswith("Z"):
            raise DecodeError("Observation time needs to end with Z")
        return super()._decode(dt)
    def _encode(self, data):
        return "{}Z".format(super()._encode(data))
class PresentWeather(Observation):
    """
    Present weather
    """
    _ENCODE_DEFAULT = None
    def _decode(self, ww):
        if ww == "NSW":
            return { "no_significant_weather": True }
        else:
            return ct.CodeTable4678().decode(ww)
    def _encode(self, data):
        weather = []
        for d in data:
            if "no_significant_weather" in d and d["no_significant_weather"]:
                weather.append("NSW")
            else:
                weather.append(ct.CodeTable4678().encode(d))
        return " ".join(weather)
class QNH(Observation):
    """
    QNH

    PPPP - QNH value
    """
    _ENCODE_DEFAULT = "Q////"
    _CONVERSION = {
        "Q": ("hPa", 1),
        "A": ("inHg", 0.01)
    }
    def _decode(self, qnh):
        try:
            unit = self._CONVERSION[qnh[0]][0]
            val  = int(qnh[1:]) * self._CONVERSION[qnh[0]][1]
            return { "value": val, "unit": unit }
        except Exception as e:
            return { "value": None, "unit": "hPa" }
    def _encode(self, data):
        prefix = None
        for k, v in self._CONVERSION.items():
            if v[0] == data["unit"]:
                prefix = k
                qnh = int(data["value"] / v[1])
                break
        if prefix is None:
            raise EncodeError("{} is an invalid unit for QNH".format(data["unit"]))

        return "{Q}{qnh}".format(
            Q = prefix,
            qnh = "{:04d}".format(qnh)
        )
class RecentWeather(Observation):
    """
    Recent weather phenomena of operational significance
    """
    def _decode(self, ww):
        code_table = ct.CodeTable4678().decode(ww)
        del(code_table["intensity"])
        return code_table
    def _encode(self, data):
        return "RE{ww}".format(
            ww = ct.CodeTable4678().encode(data)
        )
class Remarks(Observation):
    """
    Remarks which appear at the end of a METAR
    """
    _ENCODE_DEFAULT = "RMK"
    def _decode(self, remarks):
        return " ".join(remarks)
    def _encode(self, data):
        return "RMK {}".format(data)
class RunwayVisual(Observation):
    """
    Runway visual observation
    """
    def _decode(self, rvr):
        # (runway, vis) = rvr.split("/")
        try:
            groups = re.match(r"^R((0?[1-9]|[1-2]\d|3[0-6])[LCR]?)\/([PM]?)(\d{4}|\/{4})([UDN]?|FT)(V([PM]?)(\d{4}|\/{4})([UDN]?|FT))?$", rvr).groups()
            # (RR, extreme_1, vis_1, tendency_1, variation, extreme_2, vis_2, tendency_2) = groups
            # print(groups)
            # (RR, extreme, vis, tendency) = re.match(r"^R(\d{2})\/([PM]?)(\d{4}|\/{4})([UDN]?)$", rvr).groups()
        except:
            raise InvalidCode(rvr, "runway visual reading")

        return {
            "runway": self.Runway().decode(groups[0]),
            "visibility": self.Visibility().decode(groups[2:])
            # "visibility": self.Visibility().decode(vis_1, extreme=[extreme_1, extreme_2], tendency=[tendency_1, tendency_2])
        }
    def _encode(self, data):
        groups = []
        for d in data:
            # print(d["visibility"])
            groups.append("R{RR}/{VVVV}".format(
                RR = self.Runway().encode(d["runway"] if "runway" in d else None),
                VVVV = self.Visibility().encode(d["visibility"] if "visibility" in d else None)
            ))
        return " ".join(groups)
    class Runway(Observation):
        def _decode(self, RR):
            return { "value": RR }
        def _encode(self, data):
            if "value" in data and re.match(r"^(0?[1-9]|[1-2]\d|3[0-6])[LCR]?$", data["value"]):
                return data["value"]
            else:
                raise InvalidCode(data["value"], "runway")
    class Visibility(Observation):
        _CODE_LEN = 4
        _UNIT = "m"
        _EXTREMES = {
            "P": "isGreaterOrEqual",
            "M": "isLessOrEqual"
        }
        _TENDENCIES = {
            "U": "up",
            "D": "down",
            "N": "none"
        }
        def _get_extreme(self, data, e):
            if len(e) == 0:
                return data           
            try:
                data["quantifier"] = self._EXTREMES[e]
            except KeyError:
                raise InvalidCode(e, "RVR extreme")           
            return data
        def _get_tendency(self, data, t):
            if len(t) == 0:
                return data           
            try:
                data["tendency"] = self._TENDENCIES[t]
            except KeyError:
                raise InvalidCode(t, "RVR tendency")
            return data
        def _decode(self, vis):
            # If there's no extreme, tendency or variation, then it's a normal visibility
            if vis[3] is None and vis[0] == "" and (vis[2] == "" or vis[2] == "FT"):
                return Visibility().decode("{}{}".format(vis[1], vis[2]))

            if vis[3] is None:
                data = {
                    "value": int(vis[1]),
                    "unit": self._UNIT if vis[2] != "FT" else "[ft_us]"
                }
                data = self._get_extreme(data, vis[0])
                if vis[2] != "FT":
                    data = self._get_tendency(data, vis[2]) 
            else:
                data = {
                    "variation": {
                        "min": { "value": int(vis[1]), "unit": self._UNIT },
                        "max": { "value": int(vis[5]), "unit": self._UNIT }
                    }
                }
                data["variation"]["min"] = self._get_extreme(data["variation"]["min"], vis[0])
                data["variation"]["max"] = self._get_extreme(data["variation"]["max"], vis[4])
                data["variation"]["min"] = self._get_tendency(data["variation"]["min"], vis[2])
                data["variation"]["max"] = self._get_tendency(data["variation"]["max"], vis[6])

            return data
        def _encode(self, data):
            output = ""
            if "variation" not in data:
                try:
                    output += [x for x in self._EXTREMES if self._EXTREMES[x] == data["quantifier"]][0]
                except:
                    pass
                output += "{:04d}".format(data["value"])
                try:
                    if data["unit"] == "[ft_us]":
                        output += "FT"
                    else:
                        output += [x for x in self._TENDENCIES if self._TENDENCIES[x] == data["tendency"]][0]
                except:
                    pass
            else:
                v = data["variation"]
                for a in ["min", "max"]:
                    try:
                        output += [x for x in self._EXTREMES if self._EXTREMES[x] == v[a]["quantifier"]][0]
                    except:
                        pass
                    output += "{:04d}".format(v[a]["value"])
                    try:
                        output += [x for x in self._TENDENCIES if self._TENDENCIES[x] == v[a]["tendency"]][0]
                    except:
                        pass
                    if a == "min":
                        output += "V"
                
            return output
class SurfaceWind(Observation):
    """
    Surface wind
    """
    _CODE_LEN = 5
    def _decode(self, data):
        # Get direction, speed, gust and units
        ddd = data[0][0:3]
        ff  = data[0][3:5]
        if data[0][5] == "G":
            gust = data[0][6:8]
            unit = data[0][8:]
        else:
            gust = None
            unit = data[0][5:]

        # Get direction and speed
        retval = {
            "direction": self.Direction().decode(ddd),
            "speed": self.Speed().decode(ff, unit=unit),
            "gust": self.Speed().decode(gust, unit=unit),
            "variation": None
        }

        # Get variation, if required
        if len(data) > 1:
            retval["variation"] = self.Variation().decode(data[1])

        return retval
    def _encode(self, data, **kwargs):
        groups = []        
        groups.append(
            "{ddd}{ff}{gust}{unit}".format(
                ddd = self.Direction().encode(data["direction"] if "direction" in data else None, allow_none=True),
                ff = self.Speed().encode(data["speed"] if "speed" in data else None),
                gust = "" if "gust" not in data or data["gust"] is None else "G{}".format(self.Speed().encode(data["gust"])),
                unit = data["speed"]["unit"] if "speed" in data else ""
        ))
        if "variation" in data:
            if data["variation"] is not None:
                groups.append(self.Variation().encode(data["variation"] if "variation" in data else None, allow_none=True))
        
        return " ".join(groups)
    class Direction(Observation):
        _CODE_LEN = 3
        def _decode(self, ddd):
            if ddd == "VRB":
                return { "value": None, "variable": True }
            else:
                return { **DirectionDegrees().decode(ddd), "variable": False }
        def _encode(self, data, **kwargs):
            if "variable" in data and data["variable"]:
                return "VRB"
            else:
                return DirectionDegrees().encode(data)
    class Speed(Observation):
        _CODE_LEN = 2
        def _decode(self, ff, **kwargs):
            if kwargs.get("unit") in ["KT", "MPS"]:
                return { "value": int(ff), "unit": kwargs.get("unit") }
            else:
                raise InvalidCode(unit, "wind unit")
        def _encode(self, data, **kwargs):
            return "{:02d}".format(data["value"])
            # return "{ff}{unit}".format(
            #     ff = data["value"],
            #     unit = data["unit"]
            # )
    class Variation(Observation):
        _UNIT = "deg"
        def _decode(self, data):
            try:
                (dn, dx) = re.match(r"^([0-9]{3})V([0-9]*)$", data).groups()
            except Exception as e: 
                raise InvalidCode(data, "variation in wind direction")
            return { "from": int(dn), "to": int(dx), "unit": self._UNIT }
        def _encode(self, data, **kwargs):
            return "{dn}V{dx}".format(
                dn = "{:03d}".format(data["from"]),
                dx = "{:03d}".format(data["to"])
            )
# class Temperature(Observation):
#     """
#     Temperature

#     * T'T'/Td'Td' - air temperature and dew point temperature
#     """
#     _CODE_LEN = 5
    # def _decode(self, data):
    #     try:
    #         (Ts, TT, Tds, Td) = re.match(r"^(M)?(\d{2}|\/\/)\/(M)?(\d{2}|\/\/)", data).groups()
    #         TT = "{}{}".format(Ts if Ts is not None else "", TT)
    #         Td = "{}{}".format(Tds if Tds is not None else "", Td)
    #     except:
    #         raise InvalidCode(data, "temperature")
        
    #     return {
    #         "air_temperature": self.Temperature().decode(TT),
    #         "dew_point_temperature": self.Temperature().decode(Td)
    #     }
    # def _encode(self, data):
    #     return "{TT}/{Td}".format(
    #         TT = self.Temperature().encode(data["air_temperature"] if "air_temperature" in data else None),
    #         Td = self.Temperature().encode(data["dew_point_temperature"] if "dew_point_temperature" in data else None)
    #     )
class Temperature(Observation):
    _ENCODE_DEFAULT = "//"
    def _decode(self, data):
        if data.startswith("M"):
            val = int(data[1:]) * -1
        else:
            val = int(data)
        if val == 0:
            tmin = -0.5 if data.startswith("M") else 0
            tmax = 0 if data.startswith("M") else 0.5
        else:
            tmin = val - 0.5
            tmax = val + 0.5
        return { "value": val, "unit": "Cel", "min": tmin, "max": tmax }
    def _encode(self, data):
        val = round(data["value"])
        if val < 0 or "min" in data and data["min"] < 0:
            return "M{:02d}".format(abs(val))
        else:
            return "{:02d}".format(val)
class Trend(Observation):
    """
    NOSIG, TEMPO and BECMG trends
    """
    def _decode(self, trends):
        data = { "change": trends[0] }
        for t in trends[1:]:
            if re.match(r"^FM", t):
                data["from"] = self.Time().decode(t)
            elif re.match(r"^TL", t):
                data["to"] = self.Time().decode(t)
            elif re.search(r"(KT|MPS)$", t):
                data["surface_wind"] = SurfaceWind().decode([t])
            elif re.match(r"^[0-9]{4}$", t):
                data["visibility"] = Visibility().decode(t)
            elif re.match(r"^[\+\-]?([A-Z]{2})+$", t):
                if "present_weather" not in data:
                    data["present_weather"] = []
                data["present_weather"].append(PresentWeather().decode(t))
            elif re.match(r"^[A-Z]{3}", t):
                if "cloud_types" not in data:
                    data["cloud_types"] = []
                data["cloud_types"].append(CloudAmountHeight().decode(t))
        return data
    def _encode(self, data):
        out_vars = []
        for k in ["change", "from", "to", "surface_wind", "visibility", "present_weather", "cloud_types"]:
            if k not in data:
                continue
            if k == "change":
                out_vars.append(data[k])
            elif k == "from":
                out_vars.append("FM{}".format(self.Time().encode(data[k])))
            elif k == "to":
                out_vars.append("TL{}".format(self.Time().encode(data[k])))
            elif k == "surface_wind":
                out_vars.append(SurfaceWind().encode(data[k]))
            elif k == "visibility":
                out_vars.append(Visibility().encode(data[k]))
                # for v in data[k]:
                    # val = Visibility().encode(data[k])
            elif k == "present_weather":
                out_vars.append(PresentWeather().encode(data[k]))
            elif k == "cloud_types":
                out_vars.append(CloudAmountHeight().encode(data[k]))
            #     val = CloudTypes().encode(data[k])
            # out_vars.append(val)
        return " ".join(out_vars)
    class Time(Observation):
        _COMPONENTS = [
            ("hour", 2, 2, Hour),
            ("minute", 4, 2, Minute),
        ]
class VerticalVisibility(Observation):
    """
    Vertical visibility
    """
    _CODE_LEN = 3
    _CODE_TABLE = ct.CodeTable1690
    _UNIT = "m"
    def _encode(self, data):
        return "VV{:03d}".format(self._CODE_TABLE().encode(data))
class Visibility(Observation):
    """
    Visibility
    """
    _CODE_LEN = 4
    _UNIT = "m"
    def _decode(self, data):
        try:
            if data.endswith("SM"):
                # Distances in SM can be specified as fractions
                if "/" in data[0:-2]:
                    value = float(Fraction(data[0:-2]))
                else:
                    value = int(data[0:-2])
                return {
                    "value": value,
                    "unit": "[mi_us]",
                    "direction": None
                }
            elif data.endswith("FT"):
                # Visiblity measured in feet
                return {
                    "value": int(data[0:-2]),
                    "unit": "[ft_us]",
                    "direction": None
                }
            else:
                # value = int(data)
                value = int(data[0:4])
                direction = data[4:]
                if direction != "" and direction not in ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]:
                    raise DecodeError("{} is an invalid direction".format(direction))
                if 0 < value < 800:
                    increment = 50
                elif 800 <= value < 5000:
                    increment = 100
                elif 5000 <= value < 9999:
                    increment = 1000
                elif value == 9999:
                    return { "value": 10000, "unit": self._UNIT, "quantifier": "isGreaterThan", "direction": direction if direction != "" else None }
                min_val = int(value / increment) * increment
                max_val = min_val + increment
                return {
                    "value": value,
                    "min": min_val,
                    "max": max_val,
                    "unit": self._UNIT,
                    "direction": direction if direction != "" else None
                }
        except:
            raise DecodeError("Could not convert {} to a visibility value".format(value))
    def _encode(self, data):
        if "direction" not in data:
            data["direction"] = None
        if data["unit"] == "m":
            if data["value"] >= 10000:
                val = 9999
            else:
                if 0 < data["value"] < 800:
                    increment = 50
                elif 800 <= data["value"] < 5000:
                    increment = 100
                elif 5000 <= data["value"] < 9999:
                    increment = 1000
                val = int(data["value"] / increment) * increment
            if data["direction"] is not None and data["direction"] not in ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]:
                raise EncodeError("{} is an invalid direction".format(data["direction"]))
            return "{VVVV}{d}".format(
                VVVV = "{:04d}".format(val),
                d = data["direction"] if data["direction"] is not None else ""
            )
        elif data["unit"] == "[mi_us]":
            # Round according to 15.6.4 for US
            v = float(data["value"])
            if 0 <= v < 0.375:
                denom = 16
                frac  = True
            elif 0.375 <= v < 2:
                denom = 8
                frac  = True
            elif 2 <= v < 3:
                denom = 4
                frac  = True
            elif 3 <= v < 15:
                denom = 1
                frac  = False
            elif v >= 15:
                denom = 0.2
                frac  = False
            vis = (math.floor(v * denom)) / denom
            if frac:
                vis = Fraction(vis)
            else:
                vis = int(vis)

            return "{VVVV}SM".format(
                VVVV = vis
            )
        elif data["unit"] == "[ft_us]":
            # According to 15.7.2 for US, only report between 1000 and 6000
            if 0 <= data["value"] < 1000:
                return "1000FT"
            elif 1000 <= data["value"] < 6000:
                return "{VVVV}FT".format(
                    VVVV = data["value"]
                )
            elif data["value"] >= 6000:
                return "6000FT"