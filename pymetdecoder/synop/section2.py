################################################################################
# pymetdecoder/synop/section2.py
#
# Decoder routines for section 2 of a SYNOP message
#
# TDBA 2019-02-18:
#   * First version
################################################################################
# CONFIGURATION
################################################################################
import re, types, pymetdecoder
from . import code_tables as ct
################################################################################
# FUNCTIONS
################################################################################
def _encode_period_and_height(data):
    """
    Encodes wave period and height from data
    """
    PP = pymetdecoder.encode_attribute(data, "period", 2, def_unit="s", unit_type="time")
    HH = pymetdecoder.encode_attribute(data, "height", 2,
        def_unit  = "m",
        unit_type = "length",
        post_func = lambda a: abs(a * 2)
    )
    return (PP, HH)
################################################################################
# OBSERVATION CLASSES
################################################################################
class _ShipDisplacement(pymetdecoder.Observation):
    """
    Ship displacement

    * 222Dv - Direction and speed of displacement of the ship since 3 hours
    """
    _CODE = "Dv"
    _DESCRIPTION = "direction and speed of displacement of the ship since 3 hours"
    _CODE_LEN = 2
    def _decode(self, group):
        D = group[3]
        v = group[4]

        # should 22200 be decoded? it represents a stationary sea station (12.3.1.2)
        if D == "0" and v == "0":
            return None

        return {
            "direction": self.Direction().decode(D),
            "speed": self.Speed().decode(v)
        }
    def _encode(self, data, **kwargs):
        allow_none = kwargs.get("allow_none", False)
        if data is None and allow_none:
            return "00"
        else:
            return "{D}{v}".format(
                D = self.Direction().encode(data["direction"] if "direction" in data else None, allow_none=True),
                v = self.Speed().encode(data["speed"] if "speed" in data else None)
            )
    class Direction(pymetdecoder.Observation):
        _CODE = "D"
        _DESCRIPTION = "direction of displacement of the ship since 3 hours"
        _CODE_LEN = 1
        _CODE_TABLE = ct._CodeTable0700
    class Speed(pymetdecoder.Observation):
        _CODE = "v"
        _DESCRIPTION = "speed of displacement of the ship since 3 hours"
        _CODE_LEN = 1
        _CODE_TABLE = ct._CodeTable4451
class _SeaSurfaceTemperature(pymetdecoder.Observation):
    """
    Sea surface temperature

    * 0ssTTT - Sea surface temperature and its type of measurement
    """
    _CODE = "sTTT"
    _DESCRIPTION = "sea surface temperature and its type of measurement"
    _CODE_LEN = 4
    def _decode(self, group):
        # Get the values
        ss  = group[1]
        TTT = group[2:5]

        # Get sign and measurement type
        m_type = self.MeasurementType().decode(ss)

        # Return temperature and measurement type
        if m_type is None:
            return None
        else:
            temp = self.Temperature().decode(TTT, sign=m_type["sign"])
            temp["measurement_type"] = m_type["measurement_type"]
            return temp
    def _encode(self, data, **kwargs):
        return "{s}{TTT}".format(
            s   = self.MeasurementType().encode(data),
            TTT = self.Temperature().encode(data)
        )
    class MeasurementType(pymetdecoder.Observation):
        _CODE = "ss"
        _DESCRIPTION = "sea surface temperature measurement type"
        _CODE_LEN = 1
        _CODE_TABLE = ct._CodeTable3850
    class Temperature(pymetdecoder.Observation):
        _CODE = "TTT"
        _DESCRIPTION = "sea surface temperature"
        _CODE_LEN = 3
        _UNIT = "Cel"
        def _decode(self, raw, **kwargs):
            sign = kwargs.get("sign")
            return self._decode_value(raw, sign=sign)
        def _decode_convert(self, val, **kwargs):
            factor = 10 * kwargs.get("sign")
            return val / factor
        def _encode_convert(self, val, **kwargs):
            return abs(val * 10)
class _WindWaves(pymetdecoder.Observation):
    """
    Wind waves

    * 1PPHH - Period and height of waves (instrumental)
    * 2PPHH - Period and height of waves
    * 70HHH - Height of waves (instrumental)
    """
    _CODE = "PPHH"
    _DESCRIPTION = "period and height of wind waves"
    _CODE_LEN = 4
    def _decode(self, group, **kwargs):
        # Get group
        g = group[0:1]
        if g == "7":
            # This group must start with 70, otherwise it's not available
            if not group.startswith("70"):
                return None
            HHH = group[2:5]
            return {
                "period": None,
                "height": self.Height().decode(HHH, g=g),
                "instrumental": True,
                "accurate": True,
                "confused": False
            }
            # height = { "value": int(HHH) * 0.1, "unit": "m" }
            # return { "period": None, "height": height, "instrumental": True, "accurate": True }
        else:
            PP = group[1:3]
            HH = group[3:5]

        # Return period and height
        period = self.Period().decode(PP)
        if period is not None and period["value"] == 99:
            period = None
            confused = True
        else:
            confused = False
        return {
            "period": period,
            "height": self.Height().decode(HH, g=g),
            "instrumental": kwargs.get("instrumental"),
            "accurate": False,
            "confused": confused
        }
    def _encode(self, data, **kwargs):
        group = kwargs.get("_group")

        # Encode based on group
        for d in data:
            if group == "1" and "instrumental" in d and d["instrumental"]:
                return "{g}{PP}{HH}".format(
                    g  = group,
                    PP = self.Period().encode(d["period"] if "period" in d else None),
                    HH = self.Height().encode(d["height"] if "height" in d else None, g=group)
                )
            elif group == "2" and "instrumental" in d and not d["instrumental"]:
                return "{g}{PP}{HH}".format(
                    g  = group,
                    PP = self.Period().encode(d["period"] if "period" in d else None),
                    HH = self.Height().encode(d["height"] if "height" in d else None, g=group)
                )
            elif group == "7" and "accurate" in d and d["accurate"]:
                return "{g}0{HHH}".format(
                    g   = group,
                    HHH = self.Height().encode(d["height"] if "height" in d else None, g=group)
                )
        return None
    class Period(pymetdecoder.Observation):
        _CODE = "PP"
        _DESCRIPTION = "period of wind waves"
        _CODE_LEN = 2
        _UNIT = "s"
    class Height(pymetdecoder.Observation):
        _CODE = "HH"
        _DESCRIPTION = "height of wind waves"
        _CODE_LEN = 2
        _UNIT = "m"
        def _decode_convert(self, val, **kwargs):
            group = kwargs.get("g")
            if group == "7":
                factor = 0.1
            else:
                factor = 0.5
            return float("{:.1f}".format(int(val) * factor))
        def _encode_convert(self, val, **kwargs):
            group = kwargs.get("g")
            if group == "7":
                factor = 10
                self._CODE_LEN = 3
            else:
                factor = 2
            return int(val * factor)
class _SwellWaves(pymetdecoder.Observation):
    """
    Swell waves

    * 3dddd - Direction of swell eaves
    * 4PPHH - Period and height of first swell waves
    * 5PPHH - Period and height of second swell waves
    """
    _DESCRIPTION = "direction, period and height of swell waves"
    def _decode(self, group, **kwargs):
        # Split group into separate groups
        (dir_group, info_group) = group.split(" ")

        # Get direction
        if info_group.startswith("4"):
            dir = dir_group[1:3] if dir_group is not None else None
        elif info_group.startswith("5"):
            dir = dir_group[3:5] if dir_group is not None else None
        else:
            raise pymetdecoder.DecodeError("{} is not a valid swell wave group".format(g))
            return None

        # Get data and return
        output = {
            "direction": self.Direction().decode(dir),
            "period": self.Period().decode(info_group[1:3]),
            "height": self.Height().decode(info_group[3:5])
        }
        return output
    def _encode(self, data, **kwargs):
        dirs = ["//", "//"]
        waves = [None, None]
        for idx, d in enumerate(data):
            # Convert direction
            dirs[idx] = self.Direction().encode(d["direction"] if "direction" in d else None)

            # Convert wave
            waves[idx] = "{g}{PP}{HH}".format(
                g  = idx + 4,
                PP = self.Period().encode(d["period"] if "period" in d else None),
                HH = self.Height().encode(d["height"] if "height" in d else None)
            )

        # Assemble the codes
        output = ["3{}{}".format(*dirs)]
        output.extend([w for w in waves if w is not None])
        return " ".join(output)
    class Direction(pymetdecoder.Observation):
        _CODE = "dd"
        _DESCRIPTION = "direction of swell waves"
        _CODE_LEN = 2
        _CODE_TABLE = ct._CodeTable0877
        _UNIT = "deg"
    class Period(pymetdecoder.Observation):
        _CODE = "PP"
        _DESCRIPTION = "period of swell waves"
        _CODE_LEN = 2
        _UNIT = "s"
    class Height(pymetdecoder.Observation):
        _CODE = "HH"
        _DESCRIPTION = "height of swell waves"
        _CODE_LEN = 2
        _UNIT = "m"
        def _decode_convert(self, val, **kwargs):
            return int(val) * 0.5
        def _encode_convert(self, val, **kwargs):
            return int(val * 2)
class _IceAccretion(pymetdecoder.Observation):
    """
    Ice accretion

    * 6IEER - Ice accretion
    """
    _CODE = "IEER"
    _DESCRIPTION = "ice accretion"
    _CODE_LEN = 4
    def _decode(self, group):
        # Get the values
        I  = group[1]
        EE = group[2:4]
        R  = group[4]

        # Return data
        return {
            "source": self.Source().decode(I),
            "thickness": self.Thickness().decode(EE),
            "rate": self.Rate().decode(R)
        }
    def _encode(self, data, **kwargs):
        return "{I}{EE}{R}".format(
            I  = self.Source().encode(data["source"] if "source" in data else None),
            EE = self.Thickness().encode(data["thickness"] if "thickness" in data else None),
            R  = self.Rate().encode(data["rate"] if "rate" in data else None)
        )
    class Source(pymetdecoder.Observation):
        _CODE = "I"
        _DESCRIPTION = "ice accretion source"
        _CODE_LEN = 1
        _CODE_TABLE = ct._CodeTable1751
    class Thickness(pymetdecoder.Observation):
        _CODE = "EE"
        _DESCRIPTION = "ice accretion thickness"
        _CODE_LEN = 2
        _UNIT = "cm"
    class Rate(pymetdecoder.Observation):
        _CODE = "R"
        _DESCRIPTION = "ice accretion rate"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 4)
class _WetBulbTemperature(pymetdecoder.Observation):
    """
    Wet bulb temperature

    * 8sTTT - Wet bulb temperature
    """
    _CODE = "sTTT"
    _DESCRIPTION = "wet bulb temperature"
    _CODE_LEN = 4
    def _decode(self, group):
        # Get values
        s   = group[1]
        TTT = group[2:5]

        # Get sign, measured and ice status
        status = self.Status().decode(s)

        # Return temperature and measurement type
        try:
            sign = status["sign"]
        except Exception:
            sign = None
        temp = self.Temperature().decode(TTT, sign=sign)
        if temp is not None:
            temp.update(status)
        return temp
    def _encode(self, data, **kwargs):
        return "{s}{TTT}".format(
            s   = self.Status().encode(data),
            TTT = self.Temperature().encode(data)
        )
    class Status(pymetdecoder.Observation):
        _CODE = "s"
        _DESCRIPTION = "sign and type of wet bulb temperature"
        _CODE_LEN = 1
        _CODE_TABLE = ct._CodeTable3855
    class Temperature(pymetdecoder.Observation):
        _CODE = "TTT"
        _DESCRIPTION = "wet bulb temperature"
        _CODE_LEN = 3
        _UNIT = "Cel"
        def _decode(self, raw, **kwargs):
            sign = kwargs.get("sign")
            return self._decode_value(raw, sign=sign)
        def _decode_convert(self, val, **kwargs):
            factor = 10 * kwargs.get("sign")
            return val / factor
        def _encode_convert(self, val, **kwargs):
            return abs(val * 10)
class _SeaLandIce(pymetdecoder.Observation):
    """
    Sea/land ice information

    * ICE cSbDz / text - Ice information
    """
    _CODE = "ICE xxxxx"
    _DESCRIPTION = "ice information"
    _CODE_LEN = 5
    _ENCODE_DEFAULT = "ICE /////"
    def _decode(self, group):
        # Get ice groups
        ice_groups = group[1:]

        # Check availability
        if not self.is_available(ice_groups[0]):
            return None

        # cSbDz
        # If ice groups consist of one group and it's 5 digits long, assume it's
        # cSbDz. Otherwise, it's plain text
        if len(ice_groups) == 1 and self.is_available(ice_groups[0]) and len(ice_groups[0]) == 5:
            # Get the values
            (c, S, b, D, z) = list(ice_groups[0])

            # Return values
            return {
                "concentration":   self.Concentration().decode(c),
                "development":     self.Development().decode(S),
                "land_origin":     self.LandOrigin().decode(b),
                "direction":       self.Direction().decode(D),
                "condition_trend": self.ConditionTrend().decode(z)
            }
        else:
            return { "text": " ".join(ice_groups) }
    def _encode(self, data, **kwargs):
        # If text, return plain text. Otherwise, encode
        if "text" in data:
            return "ICE {}".format(data["text"])
        else:
            return "ICE {C}{S}{b}{D}{z}".format(
                C = self.Concentration().encode(data["concentration"] if "concentration" in data else None),
                S = self.Development().encode(data["development"] if "development" in data else None),
                b = self.LandOrigin().encode(data["land_origin"] if "land_origin" in data else None),
                D = self.Direction().encode(data["direction"] if "direction" in data else None),
                z = self.ConditionTrend().encode(data["condition_trend"] if "condition_trend" in data else None),
            )
    class Concentration(pymetdecoder.Observation):
        _CODE = "c"
        _DESCRIPTION = "concentration or arrangment of sea ice"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 9)
    class Development(pymetdecoder.Observation):
        _CODE = "S"
        _DESCRIPTION = "stage of development"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 9)
    class LandOrigin(pymetdecoder.Observation):
        _CODE = "b"
        _DESCRIPTION = "ice of land origin"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 9)
    class Direction(pymetdecoder.Observation):
        _CODE = "D"
        _DESCRIPTION = "bearing of ice edge"
        _CODE_LEN = 1
        _CODE_TABLE = ct._CodeTable0739
    class ConditionTrend(pymetdecoder.Observation):
        _CODE = "z"
        _DESCRIPTION = "present ice situation and trend of conditions over preceding three hours"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 9)
################################################################################
# OBSERVATION FUNCTIONS
################################################################################
def _ship_displacement(group):
    """
    Ship displacement

    * 222Dv - Direction and speed of displacement of the ship since 3 hours
    """
    Dv = group[3:5]
    obs = pymetdecoder.Observation(Dv, noValAttr=True)
    try:
        # Set availability
        if not obs.isAvailable(value=Dv):
            obs.available = False

        # Set the values
        D = Dv[0]
        v = Dv[1]

        # Get direction
        direction = ct.codeTable0700(D)
        obs.direction = pymetdecoder.Observation(D, value=direction[0])
        obs.direction.isStationary  = direction[1]
        obs.direction.allDirections = direction[2]

        # Get speeds
        units = ["KT", "km/h"]
        vals  = []
        for i, s in enumerate(ct.codeTable4451(v)):
            speed_ob = pymetdecoder.Observation("", unit=units[i], noValAttr=True)
            speed_ob.min = s[0]
            speed_ob.max = s[1]
            speed_ob.quantifier = s[2]
            speed_ob.available = True
            delattr(speed_ob, "raw")
            vals.append(speed_ob)
        obs.speed = vals
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode ship displacement group {}".format(group))

    # Return the observation
    return obs
def _sea_surface_temperature(group):
    """
    Sea surface temperature

    * 0ssTTT - Sea surface temperature and its type of measurement
    """
    obs = pymetdecoder.Observation(group, unit="Cel")
    try:
        # Set availability
        if not obs.isAvailable(value=group[2:5]):
            obs.available = False

        # Get the values
        ss  = group[1:2]
        TTT = group[2:5]

        # Set the values
        (method, sign) = ct.codeTable3850(ss)
        obs.measurementType = pymetdecoder.Observation(ss, value=method)
        if obs.available:
            obs.setValue((int(TTT) / 10.0) * sign)
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode sea surface temperature group {}".format(group))

    # Return the observation
    return obs
def _wind_waves(group, instrumental):
    """
    Wind waves

    * 1PPHH - Period and height of waves (instrumental)
    * 2PPHH - Period and height of waves
    * 70HHH - Height of waves (instrumental)

    :param string/int raw: Raw value of observation
    :param boolean instrumental: True if observation was made with an instrument, False otherwise
    """
    obs = pymetdecoder.Observation(group, noValAttr=True)
    obs.instrumental = instrumental
    try:
        # Set availability
        if not obs.isAvailable(value=group[2:5]):
            obs.available = False

        # Get the group number
        g = group[0:1]

        # Get the values
        if g == "7":
            if group[0:2] != "70":
                obs.available = False
            else:
                HHH = group[2:5]
                obs.height = pymetdecoder.Observation(HHH, unit="m")
                if obs.height.available:
                    obs.height.setValue(int(HHH) / 10.0)
                obs.period = None
        else:
            PP = group[1:3]
            HH = group[3:5]

            # Set the values
            obs.period = pymetdecoder.Observation(PP, unit="s")
            obs.height = pymetdecoder.Observation(HH, unit="m")
            if obs.period.available:
                obs.period.setValue(int(PP))
            if obs.height.available:
                obs.height.setValue(int(HH) / 2.0)
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode wind wave group {}".format(group))

    # Return the observation
    return obs
def _swell_waves(group):
    """
    Swell waves

    * 3dddd - Direction of swell eaves
    * 4PPHH - Period and height of first swell waves
    * 5PPHH - Period and height of second swell waves
    """
    obs = pymetdecoder.Observation(group, noValAttr=True)
    try:
        # Initialise array
        obs.value = []

        # Split raw into groups
        groups = group.split(" ")

        # Get directions
        dirs = [groups[0][1:3], groups[0][3:5]]

        # Loop through groups
        for i in range(1, len(groups)):
            wave_ob = pymetdecoder.Observation(None, noValAttr=True)

            dd = dirs[i - 1]
            PP = groups[i][1:3]
            HH = groups[i][3:5]

            # Get values
            wave_ob.direction = pymetdecoder.Observation(dd, unit="deg")
            wave_ob.period = pymetdecoder.Observation(PP, unit="s")
            wave_ob.height = pymetdecoder.Observation(HH, unit="m")

            # Set values
            if wave_ob.direction.available:
                wave_ob.direction.setValue(int(dd) * 10)
            if wave_ob.period.available:
                wave_ob.period.setValue(int(PP))
            if wave_ob.height.available:
                wave_ob.height.setValue(int(HH) / 2.0)
            delattr(wave_ob, "raw")
            obs.value.append(wave_ob)
    except Exception as e:
        print(str(e))
        raise pymetdecoder.DecodeError("Unable to decode swell wave group {}".format(group))

    # Return the observation
    return obs
def _ice_accretion(group):
    """
    Ice accretion on ships

    * 6IEER - Ice accretion
    """
    obs = pymetdecoder.Observation(group, noValAttr=True)
    try:
        # Set availability
        if not obs.isAvailable(value=group[1:5]):
            obs.available = False

        # Get the values
        I  = group[1:2]
        EE = group[2:4]
        R  = group[4:5]

        # Set the values
        obs.source    = pymetdecoder.Observation(I)
        obs.thickness = pymetdecoder.Observation(EE, unit="cm")
        obs.rate      = pymetdecoder.Observation(R)
        if obs.source.available:
            obs.source.setValue(ct.checkRange(I, "1751", min=1, max=5))
        if obs.thickness.available:
            obs.thickness.setValue(int(EE))
        if obs.rate.available:
            obs.rate.setValue(ct.checkRange(R, "3551", max=4))
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode ice accretion group {}".format(group))

    # Return the observation
    return obs
def _wet_bulb_temperature(group):
    """
    Wet bulb temperature

    * 8sTTT - Wet bulb temperature
    """
    obs = pymetdecoder.Observation(group, unit="Cel")
    try:
        # Set availability
        if not obs.isAvailable(value=group[2:5]):
            obs.available = False

        # Get the values
        s   = group[1:2]
        TTT = group[2:5]

        # Set the values
        (method, sign) = ct.codeTable3855(s)
        obs.measurementType = pymetdecoder.Observation(s, value=method)
        if obs.available:
            obs.setValue((int(TTT) / 10.0) * sign)
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode wet bulb temperature group {}".format(group))

    # Return the observation
    return obs
def _sea_land_ice(group):
    """
    Sea/land ice information

    * ICE xxxxx - Ice information
    """
    obs = pymetdecoder.Observation(" ".join(group), noValAttr=True)
    try:
        # Get ice groups
        iceGroups = group[1:]

        # cSbDz
        # If ice groups consist of one group and it's 5 digits long, assume it's
        # cSbDz. Otherwise, it's plain text
        if len(iceGroups) == 1 and obs.isAvailable(value=iceGroups[0]) and len(iceGroups[0]) == 5:
            # Get the values
            c = iceGroups[0][0]
            S = iceGroups[0][1]
            b = iceGroups[0][2]
            D = iceGroups[0][3]
            z = iceGroups[0][4]

            # Set the values
            obs.concentration  = ct.checkRange(c, "0639", max=9)
            obs.development    = ct.checkRange(S, "3739", max=9)
            obs.landOrigin     = ct.checkRange(b, "0439", max=9)
            obs.conditionTrend = ct.checkRange(z, "5239", max=9)
            obs.iceEdgeBearing = pymetdecoder.Observation(D, value="")
            dir, inShore, inIce = ct.codeTable0739(D)
            obs.iceEdgeBearing.value   = dir
            obs.iceEdgeBearing.inShore = inShore
            obs.iceEdgeBearing.inIce   = inIce
        else:
            obs.text = " ".join(iceGroups)
    except Exception as e:
        print(str(e))
        raise pymetdecoder.DecodeError("Unable to decode ice group {}".format(group))

    # Return the observation
    return obs
