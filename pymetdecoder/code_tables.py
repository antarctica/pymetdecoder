################################################################################
# pymetdecoder/synop/code_tables.py
#
# Code tables for decoding SYNOPs
#
# TDBA 2019-01-18:
#   * First version
################################################################################
# CONFIGURATION
################################################################################
import pymetdecoder, re, logging, sys
################################################################################
# FUNCTIONS
################################################################################
def check_range(x, table, min=0, max=0, nullChar="/"):
    """
    Function to check if a given value is in the allowed range for the code table

    :param string x: Value to check
    :param string table: Code table
    :param int min: Minimum value
    :param int max: Maximum value
    :param string nullChar: Character representing a null value (default "/")
    :returns: Integer value of x or x as string if not available
    :rtype: int or string
    :raises: pymetdecoder.DecodeError if x is invalid
    """
    try:
        # If it's a null value, return the value
        # If it's within the range, return the value as an integer
        # Otherwise, raise an exception
        if x.count(nullChar) == len(x):
            return None
        elif min <= int(x) <= max:
            return int(x)
        else:
            logging.warning("{} is not a valid code for code table {}".format(x, table))
    except Exception as e:
        logging.warning("{} is not a valid code for code table {}".format(x, table))
################################################################################
# BASE CLASSES
################################################################################
class CodeTable(object):
    """
    Base class for code table object
    """
    def __init__(self):
        pass
    def decode(self, value, **kwargs):
        """
        Decodes raw value into observation value(s)
        """
        try:
            return self._decode(value, **kwargs)
        except NotImplementedError as e:
            logging.error(str(e))
            sys.exit(1)
        except ValueError as e:
            logging.warning("{} is not a valid code for {}".format(str(e), type(self).__name__))
            return None
        except IndexError as e:
            logging.warning("{} is not a valid code for {}".format(value, type(self).__name__))
        except pymetdecoder.DecodeError as e:
            logging.warning(str(e))
        except Exception as e:
            # print(str(e))
            raise pymetdecoder.DecodeError("Unable to decode {} in {}".format(value, type(self).__name__))
            return None
    def encode(self, value, **kwargs):
        try:
            if value is None:
                return None
            if isinstance(value, dict) and "_code" in value:
                return value["_code"]
            return self._encode(value, **kwargs)
        except NotImplementedError as e:
            logging.error(str(e))
            sys.exit(1)
        except pymetdecoder.DecodeError as e:
            logging.warning(str(e))
        except Exception as e:
            logging.warning("Could not encode value {} in {}".format(value, type(self).__name__))
            raise pymetdecoder.EncodeError()
    def _decode(self, raw, **kwargs):
        """
        Actual decode function. Implement in subclass
        """
        raise NotImplementedError("_decode needs to be implemented for {}".format(type(self).__name__))
    def _encode(self, raw, **kwargs):
        """
        Actual encode function. Implement in subclass
        """
        raise NotImplementedError("_encode needs to be implemented for {}".format(type(self).__name__))
    def decode_range(self, val, data_range=None):
        """
        Decodes value based on given range
        """
        if data_range is None:
            data_range = self._RANGES
        return (data_range[val][0], data_range[val][1])
    def encode_range(self, data, data_range=None):
        """
        Encodes value based on given range
        """
        if data_range is None:
            data_range = self._RANGES

        # If value specified, calculate code accordingly
        if "value" in data:
            for idx, r in enumerate(data_range):
                if r[0] <= data <= r[1]:
                    return str(idx)

        # If min/max specified, calculate code accordingly
        if "min" in data and "max" in data:
            for idx, r in enumerate(data_range):
                if r[0] == data["min"] and r[1] == data["max"]:
                    return str(idx)

        # If we have reached this point, we can't encode
        raise pymetdecoder.DecodeError()
class CodeTableSimple(CodeTable):
    """
    Simple code table for returning a value in a given range. Used for tables
    where a value corresponds to a long description
    """
    def __init__(self, **kwargs):
        self._TABLE = kwargs.get("table")
    def _decode(self, raw):
        return { "value": int(raw) }
    def _encode(self, data):
        return str(data["value"])
class CodeTableLookup(CodeTableSimple):
    """
    Simple code table for returning a value from a list of possible values
    """
    def _decode(self, i):
        if self._VALUES[int(i)] is None:
            raise ValueError(i)
        retval = { "value": self._VALUES[int(i)] }
        if hasattr(self, "_UNIT"):
            retval["unit"] = self._UNIT
        return retval
    def _encode(self, data):
        return str(self._VALUES.index[data["value"]])
################################################################################
# CODE TABLE CLASSES
################################################################################
class CodeTable0161(CodeTable):
    """
    WMO Regional Association area in which buoy, drilling rig or oil- or gas-production
    platform has been deployed
    """
    _REGIONS = [None, "I", "II", "III", "IV", "V", "VI", "Antarctic"]
    def _decode(self, A1):
        # Check if given region is valid
        if re.match("(1[1-7]|2[1-6]|3[1-4]|4[1-8]|5[1-6]|6[1-6]|7[1-4])", A1):
            return self._REGIONS[int(A1[0:1])]
        else:
            raise ValueError(A1)
    def _encode(self, data):
        return(self._REGIONS.index(data))
class CodeTable0264(CodeTableLookup):
    """
    Standard isobaric surface for which the geopotential is reported
    """
    _VALUES = [None, 1000, 925, None, None, 500, None, 700, 850]
    _UNIT = "hPa"
class CodeTable0500(CodeTableLookup):
    """
    Genus of cloud
    """
    _VALUES = ["Ci", "Cc", "Cs", "Ac", "As", "Ns", "Sc", "St", "Cu", "Cb"]
class CodeTable0700(CodeTable):
    """
    Direction or bearing in one figure
    """
    _DIRECTIONS = [None, "NE", "E", "SE", "S", "SW", "W", "NW", "N", None]
    def _decode(self, D):
        if D == "/":
            return {
                "value": None, "isCalmOrStationary": None, "allDirections": None
            }
        isCalmOrStationary = False
        allDirections = False
        if int(D) == 0:
            isCalmOrStationary = True
        elif int(D) == 9:
            allDirections = True
        direction = self._DIRECTIONS[int(D)]

        return {
            "value": direction,
            "isCalmOrStationary": isCalmOrStationary,
            "allDirections": allDirections
        }
    def _encode(self, data):
        dir = str(self._DIRECTIONS.index(data["value"]))
        if dir is None:
            if "isCalmOrStationary" in data and data["isCalmOrStationary"]:
                return "0"
            elif "allDirections" in data and data["allDirections"]:
                return "9"
        return dir
class CodeTable0739(CodeTable):
    """
    True bearing of principle ice edge
    """
    _DIRECTIONS = [None, "NE", "E", "SE", "S", "SW", "W", "NW", "N", None]
    def _decode(self, Di):
        if Di == "/":
            return (None, None, None)

        ship_in_shore = True if int(Di) == 0 else False
        ship_in_ice   = True if int(Di) == 9 else False
        direction     = self._DIRECTIONS[int(Di)]

        return { "value": direction, "in_shore": ship_in_shore, "in_ice": ship_in_ice }
    def _encode(self, data):
        if data["value"] is not None:
            return str(self._DIRECTIONS.index(data["value"]))
        else:
            if "in_shore" in data and data["in_shore"]:
                return "0"
            if "in_ice" in data and data["in_ice"]:
                return "9"

        # If we reach this point, we can't encode
        raise pymetdecoder.EncodeError()
class CodeTable0833(CodeTable):
    """
    Duration and character of precipitation given by RRR
    """
    _RANGE = [
        (0, 1), (1, 3), (3, 6), (6, None)
    ]
    def _decode(self, d):
        d = int(d)
        (min, max, quantifier, unknown) = (None, None, None, False)
        if d == 8:
            logging.warning("{} is not a valid code for code table {}".format(d, self._TABLE))
            return None
        elif d == 9:
            unknown = True
        else:
            (min, max) = self._RANGE[d % 4]
            if max is None:
                quantifier = "isGreater"
        return { "min": min, "max": max, "quantifier": quantifier, "unknown": unknown, "unit": "h" }
    def _encode(self, data):
        pass
class CodeTable0877(CodeTable):
    """
    True direction, in tens of degrees, from which wind is blowing
    """
    def _decode(self, dd):
        calm = False
        varAllUnknown = False
        direction = None
        dd = int(dd)
        if dd == 0:
            calm = True
        elif dd == 99:
            varAllUnknown = True
        elif 1 <= dd <= 36:
            direction = dd * 10
        else:
            raise ValueError(dd)

        # Return the values
        return {
            "value": direction,
            "varAllUnknown": varAllUnknown,
            "calm": calm
        }
    def _encode(self, data):
        val = data["value"]
        code = int(val / 10) + (1 if val % 10 >= 5 else 0)
        return code
class CodeTable1004(CodeTable):
    """
    Elevation angle of the top of the cloud indicated by C
    Elevation angle of the top of the phenomenon above horizon
    """
    _ANGLES = [None, 45, 30, 20, 15, 12, 9, 7, 6, 5]
    def _decode(self, e):
        (value, quantifier, visible) = (None, None, True)
        e = int(e)
        if e == 0:
            visible = False
        if e == 1:
            quantifier = "isGreater"
        elif e == 9:
            quantifier = "isLess"
        value = self._ANGLES[e]

        return {
            "value": value, "quantifier": quantifier, "visible": visible
        }
    def _encode(self, data):
        pass
class CodeTable1600(CodeTable):
    """
    Height above surface of the base of the lowest cloud
    """
    _RANGES = [
        (0, 50),(50, 100),(100, 200),(200, 300),(300, 600),(600, 1000),
        (1000, 1500),(1500, 2000),(2000, 2500),(2500, None)
    ]
    def _decode(self, h):
        (min, max) = self.decode_range(int(h))
        if max is None:
            quantifier = "isGreaterOrEqual"
        else:
            quantifier = None
        return { "min": min, "max": max, "quantifier": quantifier }
    def _encode(self, data):
        return self.encode_range(data)
class CodeTable1677(CodeTable):
    """
    Height of base of cloud layer
    """
    _RANGE90 = [
        (0, 50), (50, 100), (100, 200), (200, 300), (300, 600),
        (600, 1000), (1000, 1500), (1500, 2000), (2000, 2500), (2500, float("inf"))
    ]
    def _decode(self, hh):
        hh = int(hh)
        quantifier = None
        if hh == 0:
            value = 30
            quantifier = "isLess"
        elif 1 <= hh <= 50:
            value = hh * 30
        elif 51 <= hh <= 55: # 51 - 55 not used
            raise ValueError(hh)
        elif 56 <= hh <= 80:
            value = (hh - 50) * 300
        elif 81 <= hh <= 88:
            value = ((hh - 80) * 1500) + 9000
        elif hh == 89:
            value = 21000
            quantifier = "isGreater"
        elif 90 <= hh <= 98:
            return {
                "min": self._RANGE90[hh - 90][0],
                "max": self._RANGE90[hh - 90][1]
            }
        elif hh == 99:
            value = self._RANGE90[9][0]
            quantifier = "isGreater"
        else:
            raise ValueError(hh)
        return { "value": value, "quantifier": quantifier }
    def _encode(self, data, use90=False):
        value = data["value"] if "value" in data else None

        # The 90-99 codes are used in special circumstances. Use those if
        # use90 is set to True
        # e.g. if observation made at sea (regulation 12.2.1.3.2)
        if use90:
            for idx, r in enumerate(self._RANGE90):
                if r[0] <= value < r[1]:
                    return str(idx + 90)
        else:
            if value < 30:
                code = 0
            elif value <= 1500:
                code = int(value / 300)
            elif value <= 9000:
                code = int(value / 300) + 50
            elif value <= 21000:
                code = int((value - 9000) / 1500) + 80
            else:
                code = 89
            return "{:02d}".format(code)

        # If we reach this point, we've been unable to encode
        raise pymetdecoder.EncodeError("Cannot encode visibility {}".format(value))
class CodeTable1751(CodeTable):
    """
    Ice accretion on ships
    """
    _VALUES = [None,
        { "spray": True,  "fog": False, "rain": False },
        { "spray": False, "fog": True,  "rain": False },
        { "spray": True,  "fog": True,  "rain": False },
        { "spray": False, "fog": False, "rain": True  },
        { "spray": True,  "fog": False, "rain": True  }
    ]
    def _decode(self, I):
        return self._VALUES[int(I)]
    def _encode(self, data):
        spray = data["spray"] if "spray" in data else None
        fog   = data["fog"] if "fog" in data else None
        rain  = data["rain"] if "rain" in data else None
        for idx, v in enumerate(self._VALUES):
            if v is None:
                continue
            if spray == v["spray"] and fog == v["fog"] and rain == v["rain"]:
                return idx
        raise Exception()
class CodeTable1806(CodeTable):
    """
    Indicator of type of instrumentation for evaporation measurement or type of
    crop for which evapotranspiration is reported
    """
    _TABLE = "1806"
    def _decode(self, i):
        if 0 <= int(i) <= 4:
            return { "value": "evaporation" }
        elif 5 <= int(i) <= 9:
            return { "value": "evapotranspiration" }
        return None
class CodeTable1861(CodeTableLookup):
    """
    Intensity of the phenomena
    """
    _VALUES = ["Slight", "Moderate", "Heavy or strong"]
class CodeTable2700(CodeTable):
    """
    Total cloud cover
    """
    def _decode(self, N):
        if int(N) == 9:
            return { "value": None, "obscured": True, "unit": "okta" }
        else:
            return { "value": int(N), "obscured": False, "unit": "okta" }
    def _encode(self, data):
        # If value is None and obscured is True, then use code 9
        if data["value"] is None:
            if data["obscured"]:
                return "9"
            else:
                raise Exception
        else:
            return str(data["value"])
class CodeTable3552(CodeTable):
    """
    Time at which precipitation given by RRR began or ended
    """
    _RANGE = [None,
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 12), (12, None)
    ]
    def _decode(self, R):
        (min, max, quantifier, unknown) = (None, None, None, False)
        R = int(R)
        if R == 9:
            unknown = True
        else:
            (min, max) = self._RANGE[R]
            if max is None:
                quantifier = "isGreater"
        return {
            "min": min, "max": max, "quantifier": quantifier, "unknown": unknown, "unit": "h"
        }
    def _encode(self, data):
        pass
class CodeTable3570(CodeTable):
    """
    Amount of precipitation or water equivalent of solid precipitation, or diameter
    of solid deposit
    """
    def _decode(self, RR):
        RR = int(RR)
        output = {
            "value": None, "non_measurable": False, "quantifier": None, "impossible": False
        }
        if 0 <= RR <= 55:
            output["value"] = RR
        elif 56 <= RR <= 90:
            output["value"] = (RR - 50) * 10
        elif 91 <= RR <= 96:
            output["value"] = (RR - 90) / 10
        elif RR == 97:
            output["non_measurable"] = True
        elif RR == 98:
            output["value"] = 400
            output["quantifier"] = "isGreater"
        elif RR == 99:
            output["non_measurable"] = True
        else:
            raise pymetdecoder.DecodeError()
        return output
    def _encode(self, data):
        pass
class CodeTable3590(CodeTable):
    """
    Amount of precipitation which has fallen during the reporting period
    """
    def _decode(self, RRR):
        RRR = int(RRR)
        if RRR <= 988:
            (val, quantifier, trace) = (RRR, None, False)
        elif RRR == 989:
            (val, quantifier, trace) = (RRR, "isGreaterOrEqual", False)
        elif RRR == 990:
            (val, quantifier, trace) = (0, None, True)
        elif 991 <= RRR <= 999:
            (val, quantifier, trace) = (float((RRR - 990) / 10.0), None, False)
        else:
            raise pymetdecoder.DecodeError("{} is not a valid precipitation code for code table 3590".format(RRR))

        # Return value
        return { "value": val, "quantifier": quantifier, "trace": trace }
    def _encode(self, data):
        # Check value was passed
        if "value" not in data:
            raise Exception
        if data["value"] < 1:
            val = (float(data["value"]) * 10) + 990
        elif 1 <= data["value"] < 989:
            val = data["value"]
        else:
            val = data["value"]
        return str("{:03d}".format(int(val)))
class CodeTable3590A(CodeTable):
    """
    Amount of precipitation which has fallen during 24 hour period
    """
    def _decode(self, RRRR):
        RRRR = int(RRRR)
        if RRRR <= 9998:
            (val, quantifier, trace) = (float("{:.1f}".format(RRRR * 0.1)), None, False)
        elif RRRR == 9998:
            (val, quantifier, trace) = (999.8, "isGreaterOrEqual", False)
        elif RRRR == 9999:
            (val, quantifier, trace) = (0, None, True)
        else:
            raise pymetdecoder.DecodeError("{} is not a valid precipitation code for code table 3590".format(RRR))

        # Return value
        return { "value": val, "quantifier": quantifier, "trace": trace }
    def _encode(self, data):
        # Check value was passed
        if "value" not in data:
            raise Exception
        if data["value"] <= 999.8:
            val = (float(data["value"]) * 10)
        elif data["trace"]:
            val = 9999
        else:
            val = data["value"]
        return str("{:04d}".format(int(val)))
class CodeTable3850(CodeTable):
    """
    Indicator for sign and type of measurement of sea surface temperature
    """
    _METHODS = ["Intake", "Bucket", "Hull contact sensor", "Other"]
    def _decode(self, ss):
        if ss == "/":
            return (None, 1)

        # Determine the method and the sign
        method = self._METHODS[(int(ss) >> 1)]
        sign   = 0 if int(ss) % 2 == 0 else 1

        # Return method and sign
        return { "value": method }
    def _encode(self, data):
        # Get measurement type from list. If not present, use Other
        if "value" in data and data["value"] in self._METHODS:
            method = data["value"]
        else:
            method = "Other"
        m = self._METHODS.index(method)

        # Convert to code value using method and sign, then return
        if data["value"] >= 0:
            return str(2 * m)
        else:
            return str((2 * m) + 1)
class CodeTable3855(CodeTable):
    """
    Indicator for the sign and type of wet-bulb temperature reported
    """
    _OUTPUTS = [
        { "sign":    1, "measured":  True, "iced": False },
        { "sign":   -1, "measured":  True, "iced": False },
        { "sign": None, "measured":  True, "iced": True  },
        None,
        None,
        { "sign":    1, "measured": False, "iced": False },
        { "sign":   -1, "measured": False, "iced": False },
        { "sign": None, "measured": False, "iced": True  }
    ]
    def _decode(self, sw):
        if sw == "/":
            return { "sign": None, "measured": None, "iced": None }

        # Return required output
        return self._OUTPUTS[int(sw)]
    def _encode(self, data):
        if "value" in data:
            factor = 10 if data["value"] >= 0 else -10

        measured = data["measured"] if "measured" in data else None
        iced = data["iced"] if "iced" in data else None
        for idx, o in enumerate(self._OUTPUTS):
            if iced and o[2]:
                if measured == o[1]:
                    return str(idx)
            else:
                if factor == o[0] and measured == o[1]:
                    return str(idx)

        # If we reach this point, raise exception
        raise Exception
class CodeTable3870(CodeTable):
    """
    Depth of newly fallen snow
    """
    def _decode(self, ss):
        ss = int(ss)
        (val, quantifier, inaccurate) = (None, None, False)
        if 0 <= ss <= 55:
            val = ss * 10
        elif 56 <= ss <= 90:
            val = (ss - 50) * 100
        elif 91 <= ss <= 96:
            val = ss - 90
        elif ss == 97:
            val = 1
            quantifier = "isLess"
        elif ss == 98:
            val = 4000
            quantifier = "isGreater"
        elif ss == 99:
            inaccurate = True
        else:
            raise Exception
        return {
            "value": val, "quantifier": quantifier, "inaccurate": inaccurate, "unit": "mm"
        }
    def _encode(self, data):
        pass
class CodeTable3889(CodeTable):
    """
    Total depth of snow
    """
    def _decode(self, sss):
        output = {
            "depth": None, "quantifier": None, "continuous": True, "impossible": False
        }
        if sss == 0:
            raise ValueError("000")
        elif sss == 997:
            output["depth"] = 0.5
            output["quantifier"] = "isLess"
        elif sss == 998:
            output["continuous"] = False
        elif sss == 999:
            output["impossible"] = True
        else:
            output["depth"] = int(sss)
        return output
    def _encode(self, data):
        if "depth" in data and data["depth"] is not None:
            if data["depth"] == 0.5:
                return 997
            else:
                return data["depth"]
        elif "continuous" in data and not data["continuous"]:
            return 998
        elif "impossible" in data and data["impossible"]:
            return 999
        else:
            raise Exception
class CodeTable4019(CodeTableLookup):
    """
    Duration of period of reference for amount of precipitation, ending at the time of the report
    """
    _VALUES = [None, 6, 12, 18, 24, 1, 2, 3, 9, 15]
    _UNIT = "h"
class CodeTable4077T(CodeTable):
    """
    Time before observation or duration of phenomena
    """
    def _decode(self, t):
        t = int(t)
        if 0 <= t <= 60:
            return { "value": 6 * t, "unit": "min" }
        elif 61 <= t <= 66:
            return { "min": t - 55, "max": t - 54, "quantifier": None, "unit": "h" }
        raise ValueError(t)
    def _encode(self, data):
        pass
class CodeTable4077Z(CodeTable):
    """
    Variation, location or intensity of phenomena
    """
    def _decode(self, z):
        z = int(z)
        if 76 <= z <= 99:
            return { "value": z }
        raise ValueError(z)
    def _encode(self, data):
        print(data)
class CodeTable4300(CodeTable):
    """
    Forecast surface visibility
    Visibility seawards (from a coastal station)
    Visibility over the water surface of an alighting area
    """
    _RANGES = [
        (0, 50), (50, 200), (200, 500), (500, 1000), (1000, 2000), (2000, 4000),
        (4000, 10000), (10000, 20000), (20000, 50000), (50000, None)
    ]
    def _decode(self, V):
        (min, max) = self.decode_range(int(V))
        quantifier = None
        if max == None:
            quantifier = "isGreater"
        return { "min": min, "max": max, "quantifier": quantifier }
    def _encode(self, data):
        return self.encode_range(data)
class CodeTable4377(CodeTable):
    """
    Horizontal visibility at surface
    """
    _RANGE90 = [
        (0, 50), (50, 200), (200, 500), (500, 1000), (1000, 2000),
        (2000, 4000), (4000, 10000), (10000, 20000), (20000, 50000), (50000, float("inf"))
    ]
    def _decode(self, VV):
        visibility = None
        quantifier = None
        VV = int(VV)
        if 51 <= VV <= 55:
            raise ValueError(VV)
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
            raise pymetdecoder.DecodeError()

        # Return the values
        use90 = True if VV >= 90 else False
        return { "value": visibility, "quantifier": quantifier, "use90": use90 }
    def _encode(self, data, use90=False):
        value = data["value"] if "value" in data else None

        # The 90-99 codes are used in special circumstances. Use those if
        # use90 is set to True
        # e.g. if observation made at sea (regulation 12.2.1.3.2)
        if use90:
            for idx, r in enumerate(self._RANGE90):
                if r[0] <= value < r[1]:
                    return str(idx + 90)
        else:
            quantifier = data["quantifier"] if "quantifier" in data else None
            if value < 100:
                code = 0
            elif value <= 5000:
                code = int(value / 100)
            elif value <= 30000:
                code = int(value / 1000) + 50
            elif value <= 70000 and quantifier is None:
                code = int(value / 5000) + 74
            else:
                code = 89
            return "{:02d}".format(code)

        # If we reach this point, we've been unable to encode
        raise pymetdecoder.EncodeError("Cannot encode visibility {}".format(value))
class CodeTable4451(CodeTable):
    """
    Ship's average speed made good during the three hours preceding the time of observation
    """
    _KT_RANGE  = [
        (0, 0), (1, 5), (6, 10), (11, 15), (16, 20), (21, 25), (26, 30),
        (31, 35), (36, 40)
    ]
    _KMH_RANGE = [(0, 0), (1, 10), (11, 19), (20, 28), (29, 37), (38, 47), (48, 56),
        (57, 65), (66, 75)
    ]
    def _decode(self, vs):
        if vs == "/":
            return None

        vs = int(vs)
        if vs == 0:
            speedKT  = { "min": 0, "max": 0, "quantifier": None }
            speedKMH = { "min": 0, "max": 0, "quantifier": None }
        elif vs == 9:
            speedKT  = { "min": 40, "max": None, "quantifier": "isGreaterThan" }
            speedKMH = { "min": 75, "max": None, "quantifier": "isGreaterThan" }
        else:
            KT  = self.decode_range(vs, self._KT_RANGE)
            KMH = self.decode_range(vs, self._KMH_RANGE)
            speedKT  = { "min": KT[0], "max": KT[1], "quantifier": None }
            speedKMH = { "min": KMH[0], "max": KMH[1], "quantifier": None }

        # Add units
        speedKT["unit"] = "KT"
        speedKMH["unit"] = "km/h"

        # Return values
        return [speedKT, speedKMH]
    def _encode(self, data):
        if isinstance(data, list):
            data = data[0]

        # Get unit. If unit not specified, assume KT
        unit = "KT"
        if "unit" in data:
            unit = data["unit"]
        if unit == "KT":
            unit_range = self._KT_RANGE
        elif unit == "km/h":
            unit_range = self._KMH_RANGE

        # Return value from range
        return self.encode_range(data, unit_range)
class CodeTable5161(CodeTableLookup):
    """
    Optical phenomena
    """
    _VALUES = [
        "Brocken spectre", "Rainbow", "Solar or lunar halo", "Parhelia or anthelia",
        "Sun pillar", "Corona", "Twilight glow", "Twilight glow on the mountains",
        "Mirage", "Zodiacal light"
    ]
