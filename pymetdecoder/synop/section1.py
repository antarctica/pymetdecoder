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
class _PrecipitationIndicator(pymetdecoder.Observation):
    """
    Precipitation indicator

    * iR(ixhVV) - Precipitation indicator
    """
    _CODE = "iR"
    _DESCRIPTION = "precipitation indicator"
    _CODE_LEN = 1
    _VALID_RANGE = (0, 4)
    def _decode(self, iR):
        return {
            "value": int(iR),
            "in_group_1": True if iR in ["0", "1"] else False,
            "in_group_3": True if iR in ["0", "2"] else False
        }
    def _encode(self, data):
        # todo: include autodetect i.e:
        # 0 if precip in section 1 and 3
        # 1 if precip in section 1
        # 2 if precip in section 3
        # 3 if precip is not in either section, but 0
        # 4 if precip is not in either section and amount is not available
        return str(data["value"])
class _WeatherIndicator(pymetdecoder.Observation):
    """
    Weather indicator

    * (iR)ix(hVV) - Weather indicator
    """
    _CODE = "ix"
    _DESCRIPTION = "weather indicator"
    _CODE_LEN = 1
    _VALID_RANGE = (1, 7)
    def _decode(self, ix):
        return {
            "value": int(ix) if ix != "/" else None,
            "automatic": False if ix == "/" or int(ix) < 3 else True
        }
class _LowestCloudBase(pymetdecoder.Observation):
    """
    Lowest cloud base

    * (iRix)h(VV) - Height above surface of the base of the lowest cloud
    """
    _CODE = "h"
    _DESCRIPTION = "height above surface of the base of the lowest cloud"
    _CODE_LEN = 1
    _CODE_TABLE = ct._CodeTable1600
    _UNIT = "m"
class _Visibility(pymetdecoder.Observation):
    """
    Visibility

    * (iRixh)VV - Horizontal visibility at surface
    """
    _CODE = "VV"
    _DESCRIPTION = "horizontal visibility at surface"
    _CODE_LEN = 2
    _CODE_TABLE = ct._CodeTable4377
    _UNIT = "m"
    def _encode(self, data, use90=None):
        if use90 is None:
            use90 = data["use90"] if "use90" in data else False
        return self._encode_value(data, use90=use90)
class _CloudCover(pymetdecoder.Observation):
    """
    Cloud cover

    * N(ddff) - Total cloud cover
    """
    _CODE = "N"
    _DESCRIPTION = "total cloud cover"
    _CODE_LEN = 1
    _CODE_TABLE = ct._CodeTable2700
    _UNIT = "okta"
class _SurfaceWind(pymetdecoder.Observation):
    """
    Surface wind

    * (N)ddff - Surface wind direction and speed
    """
    _CODE = "ddff"
    _DESCRIPTION = "surface wind direction and speed"
    _CODE_LEN = 4
    def _decode(self, ddff):
        # Get direction and speed
        dd = ddff[0:2]
        ff = ddff[2:4]

        # Get direction and speed
        direction = self.Direction().decode(dd)
        speed = self.Speed().decode(ff)

        # Perform sanity check - if the wind is calm, it can't have a speed
        if direction["calm"] and speed["value"] > 0:
            logging.warning("Wind is calm, yet has a speed (dd: {}, ff: {})".format(dd, ff))
            return None

        return {
            "direction": self.Direction().decode(dd),
            "speed": self.Speed().decode(ff)
        }
    def _encode(self, data):
        return "{dd}{ff}".format(
            dd = self.Direction().encode(data["direction"] if "direction" in data else None, allow_none=True),
            ff = self.Speed().encode(data["speed"] if "speed" in data else None)
        )
    class Direction(pymetdecoder.Observation):
        _CODE = "dd"
        _DESCRIPTION = "surface wind direction"
        _CODE_LEN = 2
        _CODE_TABLE = ct._CodeTable0877
        _UNIT = "deg"
    class Speed(pymetdecoder.Observation):
        _CODE = "ff"
        _DESCRIPTION = "surface wind speed"
        _CODE_LEN = 2
class _Temperature(pymetdecoder.Observation):
    """
    Temperature observation

    * 1sTTT - air temperature
    * 2sTTT - dewpoint temperature
    """
    _CODE = "sTTT"
    _DESCRIPTION = "temperature"
    _CODE_LEN = 4
    def _decode(self, group):
        # Get the sign (sn) and temperature (TTT):
        sn  = group[1:2]
        TTT = group[2:5]

        # The last character can sometimes be a "/" instead of a 0, so fix
        TTT = re.sub("\/$", "0", TTT)

        # Return value
        return self.Temperature().decode(TTT, sign=sn)
    def _encode(self, data, group=None):
        return "{sTTT}".format(
            sTTT = self.Temperature().encode(data)
        )
    class Temperature(pymetdecoder.Observation):
        _CODE = "TTT"
        _DESCRIPTION = "temperature"
        _CODE_LEN = 4
        _UNIT = "Cel"
        def _decode(self, raw, **kwargs):
            sign = kwargs.get("sign")
            if sign not in ["0", "1"]:
                return None
            return self._decode_value(raw, sign=sign)
        def _decode_convert(self, val, **kwargs):
            factor = 10 if kwargs.get("sign") == "0" else -10
            return val / factor
        def _encode_convert(self, val, **kwargs):
            return "{}{:03d}".format(
                0 if val >= 0 else 1,
                int(abs(val * 10))
            )
class _RelativeHumidity(pymetdecoder.Observation):
    """
    Relative humidity

    * 29UUU - relative humidity
    """
    _CODE = "UUU"
    _DESCRIPTION = "relative humidity"
    _CODE_LEN = 3
    _VALID_RANGE = (0, 100)
    _UNIT = "%"
class _Pressure(pymetdecoder.Observation):
    """
    Pressure

    * 3PPPP - Station level pressure
    * 4PPPP - Sea level pressure
    """
    _CODE = "PPPP"
    _DESCRIPTION = "pressure"
    _CODE_LEN = 4
    _UNIT = "hPa"
    def _decode_convert(self, val, **kwargs):
        return (int(val) / 10) + (0 if int(val) > 500 else 1000)
    def _encode_convert(self, val, **kwargs):
        return abs(val * 10) - (10000 if val >= 1000 else 0)
class _Geopotential(pymetdecoder.Observation):
    """
    Geopotential

    * 4ahhh - Geopotential level and height
    """
    _CODE = "ahhh"
    _DESCRIPTION = "geopotential level and height"
    _CODE_LEN = 4
    def _decode(self, group):
        a   = group[1]
        hhh = group[2:5]

        return {
            "surface": self.Surface().decode(a),
            "height": self.Height().decode(hhh, surface=a)
        }
    def _encode(self, data, **kwargs):
        surface = data["surface"] if "surface" in data else None
        return "{a}{hhh}".format(
            a   = self.Surface().encode(surface),
            hhh = self.Height().encode(data["height"] if "height" in data else None, surface=surface)
        )
    class Surface(pymetdecoder.Observation):
        _CODE = "a"
        _DESCRIPTION = "geopotential surface"
        _CODE_LEN = 1
        _CODE_TABLE = ct._CodeTable0264
    class Height(pymetdecoder.Observation):
        _CODE = "hhh"
        _DESCRIPTION = "geopotential height"
        _CODE_LEN = 3
        _UNIT = "gpm"
        def _decode_convert(self, val, **kwargs):
            surface = int(kwargs.get("surface"))
            if surface == 2:
                return val + 1000 if val < 300 else 0
            if surface == 7:
                return val + 3000 if val < 500 else 2000
            if surface == 8:
                return val + 1000
            return val
        def _encode_convert(self, val, **kwargs):
            surface = kwargs.get("surface")
            code = int(surface["_code"])
            if code == 2:
                return val - 1000 if val <= 1300 else 0
            if code == 7:
                return val - 3000 if val <= 3500 else 2000
            if code == 8:
                return val - 1000
            return val
class _PressureTendency(pymetdecoder.Observation):
    """
    Pressure tendency

    * 5appp - Pressure tendency over the past three hours
    """
    _CODE = "appp"
    _DESCRIPTION = "pressure tendency over the past three hours"
    def _decode(self, group):
        # Get the tendency and the change
        a   = group[1:2]
        ppp = group[2:5]

        # Set the values
        tendency = self.Tendency().decode(a)
        change   = self.Change().decode(ppp, tendency=tendency)
        return { "tendency": tendency, "change": change}
    def _encode(self, data, **kwargs):
        return "{a}{ppp}".format(
            a   = self.Tendency().encode(data["tendency"] if "tendency" in data else None),
            ppp = self.Change().encode(data["change"] if "change" in data else None)
        )
    class Tendency(pymetdecoder.Observation):
        _CODE = "a"
        _DESCRIPTION = "pressure tendency indicator"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 8)
    class Change(pymetdecoder.Observation):
        _CODE = "ppp"
        _DESCRIPTION = "pressure tendency change"
        _CODE_LEN = 3
        _UNIT = "hPa"
        def _decode_convert(self, val, **kwargs):
            tendency = kwargs.get("tendency")
            return (val / (10.0 if tendency["value"] < 5 else -10.0))
        def _encode_convert(self, val, **kwargs):
            return abs(val * 10)
class _Precipitation(pymetdecoder.Observation):
    """
    Precipitation

    * 6RRRt - Precipitation amount
    """
    _CODE = "RRRt"
    _DESCRIPTION = "precipitation amount"
    _CODE_LEN = 4
    def _decode(self, group):
        RRR = group[1:4]
        t   = group[4:5]
        return {
            "amount": self.Amount().decode(RRR),
            "time_before_obs": self.TimeBeforeObs().decode(t)
        }
    def _encode(self, data, **kwargs):
        return "{RRR}{t}".format(
            RRR = self.Amount().encode(data["amount"] if "amount" in data else None),
            t = self.TimeBeforeObs().encode(data["time_before_obs"] if "time_before_obs" in data else None)
        )
    class Amount(pymetdecoder.Observation):
        _CODE = "RRR"
        _DESCRIPTION = "precipitation amount"
        _CODE_LEN = 3
        _CODE_TABLE = ct._CodeTable3590
        _UNIT = "mm"
    class TimeBeforeObs(pymetdecoder.Observation):
        _CODE = "t"
        _DESCRIPTION = "time before precipitation observation"
        _CODE_LEN = 1
        _CODE_TABLE = ct._CodeTable4019
        _UNIT = "h"
class _Weather(pymetdecoder.Observation):
    """
    Weather

    * 7wwWW - Present and past weather
    """
    _CODE = "wwWW"
    _DESCRIPTION = "present and past weather"
    _CODE_LEN = 2
    def _decode(self, group, **kwargs):
        time_before = kwargs.get("time_before")

        # Initialise data
        data = { "value": int(group) }
        if time_before is not None:
            data["time_before_obs"] = time_before

        # Return data
        return data
    def _encode(self, data, **kwargs):
        weather_type = kwargs.get("weather_type")
        if weather_type == "present":
            return "{:02d}".format(data["value"])
        elif weather_type == "past":
            valstr = list("//")
            for i in range(2):
                try:
                    valstr[i] = str(data[i]["value"])
                except:
                    pass
            return "".join(valstr)
        else:
            raise pymetdecoder.DecodeError("{} is not a valid weather type".format(weather_type))
class _CloudType(pymetdecoder.Observation):
    """
    Cloud Types/Amount

    * 8NCCC - Cloud types and base of lowest cloud
    """
    _CODE = "NCCC"
    _DESCRIPTION = "cloud types and base of lowest cloud"
    _CODE_LEN = 4
    def _decode(self, group):
        # Get the components
        Nh = group[1:2] # Amount of lowest cloud if there is lowest cloud, else base of middle cloud
        CL = group[2:3] # Lowest cloud type
        CM = group[3:4] # Middle cloud type
        CH = group[4:5] # High cloud type

        # Initialise data dict
        data = {
            "low_cloud_type": self.CloudType().decode(CL),
            "middle_cloud_type": self.CloudType().decode(CM),
            "high_cloud_type": self.CloudType().decode(CH)
        }

        # Add oktas
        cover = self.CloudCover().decode(Nh)
        if Nh != "/":
            if data["low_cloud_type"] is not None and 1 <= data["low_cloud_type"]["value"] <= 9:
                data["low_cloud_amount"] = cover
            elif data["middle_cloud_type"] is not None and 0 <= data["middle_cloud_type"]["value"] <= 9:
                data["middle_cloud_amount"] = cover
            else:
                logging.warning("Cloud cover (Nh = {}) reported, but there are no low or middle clouds (CL = {}, CM = {})".format(Nh, CL, CM))
                data["cloud_amount"] = cover

        # Return data
        return data
    def _encode(self, data, **kwargs):
        cloud_cover = None
        for a in ["low_cloud_amount", "middle_cloud_amount", "cloud_amount"]:
            if a in data:
                cloud_cover = data[a]
                break
        return "{N}{CL}{CM}{CH}".format(
            N =  self.CloudType().encode(cloud_cover),
            CL = self.CloudType().encode(data["low_cloud_type"] if "low_cloud_type" in data else None),
            CM = self.CloudType().encode(data["middle_cloud_type"] if "middle_cloud_type" in data else None),
            CH = self.CloudType().encode(data["high_cloud_type"] if "high_cloud_type" in data else None),
        )
    class CloudType(pymetdecoder.Observation):
        _CODE = "C"
        _DESCRIPTION = "cloud type"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 9)
    class CloudCover(pymetdecoder.Observation):
        _CODE = "N"
        _DESCRIPTION = "cloud cover"
        _CODE_LEN = 1
        _UNIT = "okta"
class _ExactObservationTime(pymetdecoder.Observation):
    """
    Exact observation time

    * 9GGgg - Time of observation in hours and minutes and UTC
    """
    _CODE = "GGgg"
    _DESCRIPTION = "time of observation in hours and minutes and UTC"
    _CODE_LEN = 4
    def _decode(self, group):
        # Get the components
        GG = group[1:3]
        gg = group[3:5]

        # Return values
        return {
            "hour": self.Hour().decode(GG),
            "minute": self.Minute().decode(gg)
        }
    def _encode(self, data, **kwargs):
        return "{GG}{gg}".format(
            GG = self.Hour().encode(data["hour"] if "hour" in data else None),
            gg = self.Minute().encode(data["minute"] if "minute" in data else None)
        )
    class Hour(pymetdecoder.Observation):
        _CODE = "GG"
        _DESCRIPTION = "hour of observation"
        _CODE_LEN = 2
        _VALID_RANGE = (0, 24)
    class Minute(pymetdecoder.Observation):
        _CODE = "gg"
        _DESCRIPTION = "minute of observation"
        _CODE_LEN = 2
        _VALID_RANGE = (0, 59)
################################################################################
# OBSERVATION FUNCTIONS
################################################################################
def _precipitation_indicator(iR):
    """
    Precipitation indicator

    * iR(ixhVV) - Precipitation indicator
    """
    obs = pymetdecoder.Observation(iR)
    try:
        # Check indicator is valid
        if not re.match("[01234/]$", iR):
            logging.warning("{} is an invalid value for the precipitation indicator (iR)".format(iR))
            obs.available = False
            return obs

        obs.setValue(int(iR))
        obs.inGroup1 = True if obs.value in [0, 1] else False
        obs.inGroup3 = True if obs.value in [0, 2] else False
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode precipitation indicator {}".format(iR))

    # Return the observation
    return obs
def _weather_indicator(ix):
    """
    Weather indicator

    * (iR)ix(hVV) - Weather indicator
    """
    obs = pymetdecoder.Observation(ix)
    try:
        # Check indicator is valid
        if not re.match("[1234567/]$", ix):
            logging.warning("{} is an invalid value for the weather indicator (iX)".format(iX))
            self.available = False
            return obs

        obs.setValue(int(ix))
        obs.automatic = True if obs.value >= 4 else False
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode weather indicator {}".format(ix))

    # Return the observation
    return obs
def _lowest_cloud_base(h):
    """
    Lowest cloud base

    * (iRix)h(VV) - Height above surface of the base of the lowest cloud
    """
    obs = pymetdecoder.Observation(h, unit="m")
    try:
        if obs.available:
            min, max, quantifier = ct.codeTable1600(int(h))
            obs.min = min
            obs.max = max
            obs.quantifier = quantifier
        else:
            obs.min = None
            obs.max = None
            obs.quantifier = None
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode lowest cloud base {}".format(h))

    # Return the observation
    return obs
def _visibility(VV):
    """
    Visibility

    * (iRixh)VV - Horizontal visibility at surface
    """
    obs = pymetdecoder.Observation(VV, unit="m")
    try:
        if obs.available:
            visibility, quantifier = ct.codeTable4377(int(VV))
            obs.setValue(visibility)
            obs.quantifier = quantifier
        else:
            obs.quantifier = None
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode visibility {}".format(VV))

    # Return the observation
    return obs
def _cloud_cover(N):
    """
    Cloud cover

    * N(ddff) - Total cloud cover
    """
    obs = pymetdecoder.Observation(N, unit="okta")
    try:
        if obs.available:
            if int(N) == 9:
                obs.obscured = True
            else:
                obs.setValue(int(N))
                obs.obscured = False
        else:
            obs.obscured = None
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode total cloud cover {}".format(N))

    # Return the observation
    return obs
def _surface_wind(ddff):
    """
    Surface wind

    * (N)ddff - Surface wind direction and speed
    """
    obs = pymetdecoder.Observation(ddff, noValAttr=True)
    try:
        dd = ddff[0:2]
        ff = ddff[2:4]

        # Set the wind direction
        obs.direction = pymetdecoder.Observation(dd, unit="deg")
        if obs.direction.available:
            direction, calm, varAllUnknown = ct.codeTable0877(int(dd))
            obs.direction.setValue(direction)
            obs.direction.calm = calm
            obs.direction.varAllUnknown = varAllUnknown
        else:
            obs.direction.calm = None
            obs.direction.varAllUnknown = None

        # Set the wind speed
        obs.speed = pymetdecoder.Observation(ff)
        if obs.speed.available:
            obs.speed.setValue(int(ff))
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode surface wind group {}".format(ddff))

    # Return the observation
    return obs
def _temperature(group):
    """
    Temperature observation

    * 1sTTT - air temperature
    * 2sTTT - dewpoint temperature
    """
    obs = pymetdecoder.Observation(group, unit="Cel")
    try:
        # Get the sign (sn) and the temperature (TTT)
        sn  = group[1:2]
        TTT = group[2:5]

        # Set availability
        if not obs.isAvailable(value=sn) or not obs.isAvailable(value=TTT):
            obs.available = False

        # Set the values
        if obs.available:
            if TTT[2] == "/":
                TTT = TTT[0:2] + "0"
            sn = int(sn)
            TTT = int(TTT)
            if sn not in [0,1]:
                logging.warning("{} is not a valid temperature sign code for code table 3845".format(sn))

            # Set the value
            obs.setValue((TTT / 10.0) * (1 if sn == 0 else -1))
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode temperature group {}".format(group))

    # Return the observation
    return obs
def _relative_humidity(group):
    """
    Relative humidity

    * 29UUU - relative humidity
    """
    obs = pymetdecoder.Observation(group, unit="%")
    try:
        # Get the relative humidity
        UUU = group[2:5]

        # Set the values
        if obs.available:
            UUU = int(UUU)
            if UUU > 100:
                raise pymetdecoder.DecodeError("{} is not a valid relative humidity".format(humidity))
            obs.setValue(UUU)
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode relative humidity group {}".format(group))

    # Return the observation
    return obs
def _pressure(group):
    """
    Pressure

    * 3PPPP - Station level pressure
    * 4PPPP - Sea level pressure
    """
    obs = pymetdecoder.Observation(group, unit="hPa")
    try:
        # Set availability
        PPPP = group[1:5]
        if not obs.isAvailable(value=PPPP):
            obs.available = False

        # Set the value
        if obs.available:
            PPPP = int(PPPP)
            obs.setValue((PPPP / 10) + (0 if PPPP > 500 else 1000))
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode pressure group {}".format(groups))

    # Return the observation
    return obs
def _geopotential(group):
    """
    Geopotential

    * 4ahhh - Geopotential level and height
    """
    obs = pymetdecoder.Observation(group, noValAttr=True)
    try:
        # Get the surface data
        a = group[1]
        obs.surface = pymetdecoder.Observation(a, unit="hPa")
        if obs.surface.available:
            obs.surface.setValue(ct.codeTable0264(int(a)))

        # Get the height data
        hhh = group[2:5]
        obs.height = pymetdecoder.Observation(hhh, unit="gpm")
        if obs.height.available:
            a = int(a)
            hhh = int(hhh)
            if a == 2:
                hhh += 1000 if hhh < 300 else 0
            elif a == 7:
                hhh += 3000 if hhh < 500 else 2000
            elif a == 8:
                hhh += 1000
            obs.height.setValue(hhh)
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode geopotential group {}".format(group))

    # Return the observation
    return obs
def _pressure_tendency(group):
    """
    Pressure tendency

    * 5appp - Pressure tendency over the past three hours
    """
    obs = pymetdecoder.Observation(group, noValAttr=True)
    obs.tendency = None
    obs.change = None
    try:
        # Set availability
        if not obs.isAvailable(value=group[1:5]):
            obs.available = False

        # Set the value
        if obs.available:
            a   = group[1:2]
            ppp = group[2:5]
            # Check indicator is valid
            if not re.match("[012345678/]$", a):
                logging.warning("{} is an invalid value for the tendency indicator (a)".format(a))
                return obs
            obs.tendency = pymetdecoder.Observation(a)
            obs.tendency.setValue(None if a == "/" else int(a))
            obs.change = pymetdecoder.Observation(ppp, unit="hPa")
            if obs.tendency.available and obs.change.available:
                obs.change.setValue(float("{:.1f}".format(int(ppp) / (10.0 if obs.tendency.value < 5 else -10.0))))
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode pressure tendency group {}".format(group))

    # Return the observation
    return obs
def _precipitation(group):
    """
    Precipitation

    * 6RRRt - Precipitation amount
    """
    obs = pymetdecoder.Observation(group)
    try:
        # Get the precipitation data
        RRR = group[1:4]
        obs.amount = pymetdecoder.Observation(RRR, unit="mm")
        if obs.amount.available:
            value, quantifier, trace = ct.codeTable3590(int(RRR))
            obs.amount.setValue(value)
            obs.amount.quantifier = quantifier
            obs.amount.trace = trace

        # Get the time before obs
        t = group[4:5]
        obs.timeBeforeObs = pymetdecoder.Observation(t, unit="h")
        if obs.timeBeforeObs.available:
            if int(t) == 0:
                obs.timeBeforeObs.available = False
            else:
                obs.timeBeforeObs.setValue(ct.codeTable4019(int(t)))

        # Tidy attributes
        # delattr(self, "available")
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode precipitation group {}".format(group))

    # Return the observation
    return obs
def _weather(ww):
    """
    Weather

    * 7wwWW - Present and past weather
    """
    obs = pymetdecoder.Observation(ww)
    try:
        if obs.available:
            obs.setValue(int(ww))
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode weather group {}".format(ww))

    # Return the observation
    return obs
def _cloud_types(group):
    """
    Cloud Types/Amount

    * 8Nhhh - Cloud types and base of lowest cloud
    """
    obs = pymetdecoder.Observation(group, noValAttr=True)
    try:
        # Set availability
        if not obs.isAvailable(value=group[1:5]):
            obs.available = False

        # Get the components
        Nh = group[1:2] # Amount of lowest cloud if there is lowest cloud, else base of middle cloud
        CL = group[2:3] # Lowest cloud type
        CM = group[3:4] # Middle cloud type
        CH = group[4:5] # High cloud type

        # Check if sky obscured or observation not made
        obs.obscured = True if Nh == 9 else False

        # Get the cloud types
        obs.lowCloudType    = _setCloudValue(CL)
        obs.middleCloudType = _setCloudValue(CM)
        obs.highCloudType   = _setCloudValue(CH)

        # Add the oktas
        if Nh != "0" and Nh != "/":
            if obs.lowCloudType.available and 1 <= obs.lowCloudType.value <= 9:
                obs.lowCloudCover = pymetdecoder.Observation(Nh, value=int(Nh), unit="okta")
            elif obs.middleCloudType.available and 1 <= obs.middleCloudType.value <= 9:
                obs.middleCloudCover = pymetdecoder.Observation(Nh, value=int(Nh), unit="okta")
            else:
                logging.warning("Cloud cover (Nh = {}) reported, but there are no low or middle clouds (CL = {}, CM = {})".format(Nh, CL, CM))
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode cloud type/amount group {}".format(group))

    # Return the observation
    return obs
def _exact_observation_time(group):
    """
    Exact observation time

    * 9GGgg - Time of observation in hours and minutes and UTC
    """
    obs = pymetdecoder.Observation(group)
    try:
        # Set availability
        if not obs.isAvailable(value=group[1:5]):
            obs.available = False

        # Get the components
        GG = group[1:3]
        gg = group[3:5]

        # Check if values are valid
        if obs.available:
            if int(GG) > 24:
                raise pymetdecoder.DecodeError("Exact observation hour is out of range (GG = {})".format(GG))
            if int(gg) > 60:
                raise pymetdecoder.DecodeError("Exact observation minute is out of range (gg = {})".format(gg))

        # Set values
        obs.hour   = pymetdecoder.Observation(GG, value=int(GG))
        obs.minute = pymetdecoder.Observation(gg, value=int(gg))
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode exact observation time group {}".format(self.raw))

    # Return the observation
    return obs
################################################################################
# EXTRA FUNCTIONS
################################################################################
def _setCloudValue(val):
    try:
        obs = pymetdecoder.Observation(val, value=int(val))
    except:
        obs = pymetdecoder.Observation(val, value=val)
    return obs
