################################################################################
# pymetdecoder/synop/section3.py
#
# Decoder routines for section 3 of a SYNOP message
#
# TDBA 2019-05-30:
#   * First version
################################################################################
# CONFIGURATION
################################################################################
import re, types, pymetdecoder
from . import section1 as s1
from . import code_tables as ct
################################################################################
# OBSERVATION CLASSES
################################################################################
class _GroundState(pymetdecoder.Observation):
    """
    Ground state without snow or measurable ice cover

    * 3EsTT - Ground state and temperature of ground
    """
    _CODE = "EsTT"
    _DESCRIPTION = "ground state and temperature of ground"
    _CODE_LEN = 4
    def _decode(self, group):
        # Get values
        E  = group[1:2]
        s  = group[2:3]
        TT = group[3:5]

        # Return values
        return {
            "state": self.State().decode(E),
            "temperature": self.Temperature().decode(TT, sign=s)
        }
    def _encode(self, data, **kwargs):
        return "{E}{sTT}".format(
            E   = self.State().encode(data["state"] if "state" in data else None),
            sTT = self.Temperature().encode(data["temperature"] if "temperature" in data else None)
        )
    class State(pymetdecoder.Observation):
        _CODE = "E"
        _DESCRIPTION = "state of the ground without snow or measurable ice cover"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 9)
    class Temperature(pymetdecoder.Observation):
        _CODE = "TT"
        _DESCRIPTION = "temperature"
        _CODE_LEN = 3
        _UNIT = "Cel"
        def _decode(self, raw, **kwargs):
            sign = kwargs.get("sign")
            if sign not in ["0", "1"]:
                return None
            return self._decode_value(raw, sign=sign)
        def _decode_convert(self, val, **kwargs):
            factor = 1 if kwargs.get("sign") == "0" else -1
            return val / factor
        def _encode_convert(self, val, **kwargs):
            return "{}{:02d}".format(
                0 if val >= 0 else 1,
                int(abs(val))
            )
class _GroundStateSnow(pymetdecoder.Observation):
    """
    Ground state with snow or measurable ice cover

    * 4Esss - Ground state and depth of snow
    """
    _CODE = "Esss"
    _DESCRIPTION = "ground state and depth of snow"
    _CODE_LEN = 4
    def _decode(self, group):
        # Get state and temperature
        E   = group[1:2]
        sss = group[2:5]

        # Return values
        return {
            "state": self.State().decode(E),
            "depth": self.Depth().decode(sss)
        }
    def _encode(self, data, **kwargs):
        return "{E}{sss}".format(
            E   = self.State().encode(data["state"] if "state" in data else None),
            sss = self.Depth().encode(data["depth"] if "depth" in data else None)
        )
    class State(pymetdecoder.Observation):
        _CODE = "E"
        _DESCRIPTION = "state of the ground with snow or measurable ice cover"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 9)
    class Depth(pymetdecoder.Observation):
        _CODE = "sss"
        _DESCRIPTION = "depth of snow"
        _CODE_LEN = 3
        _CODE_TABLE = ct._CodeTable3889
        _UNIT = "cm"
class _Evapotranspiration(pymetdecoder.Observation):
    """
    Daily amount of evaporation or evapotranspiration

    * 5EEEi -Amount of evaporation or evapotranspiration
    """
    _CODE = "EEEi"
    _DESCRIPTION = "amount of evaporation or evapotranspiration"
    _CODE_LEN = 4
    def _decode(self, group):
        # Get state and temperature
        EEE = group[1:4]
        i   = group[4:5]

        # Return values
        return {
            "amount": self.Amount().decode(EEE),
            "type": self.TransType().decode(i)
        }
    def _encode(self, data, **kwargs):
        return "{EEE}{i}".format(
            EEE = self.Amount().encode(data["amount"] if "amount" in data else None),
            i   = self.TransType().encode(data["type"] if "type" in data else None)
        )
    class Amount(pymetdecoder.Observation):
        _CODE = "EEE"
        _DESCRIPTION = "amount of evaporation or evapotranspiration"
        _CODE_LEN = 3
        _UNIT = "mm"
        def _decode_convert(self, val):
            return val / 10
        def _encode_convert(self, val):
            return int(val * 10)
    class TransType(pymetdecoder.Observation):
        _CODE = "i"
        _DESCRIPTION = "evaporation type"
        _CODE_LEN = 1
        _CODE_TABLE = ct._CodeTable1806
class _Sunshine(pymetdecoder.Observation):
    """
    Amount of sunshine

    * 5[0123]SS - Amount of sunshine
    """
    _CODE = "SSS"
    _DESCRIPTION = "amount of sunshine"
    _CODE_LEN = 3
    def _decode(self, group):
        # Get sunshine
        SSS = group[2:5]

        # Determine if sunshine is over 24 hours (55[012]xx) or 1 hour (553xx)
        if group[2] in ["0", "1", "2"]:
            duration = { "value": 24, "unit": "h" }
        elif group[2] == "3":
            duration = { "value": 1, "unit": "h" }
        elif group[2] == "/":
            return None
        else:
            raise pymetdecoder.DecodeError("{} is not a valid value for sunshine group duration".format(group[2]))

        # Get number of hours
        if duration["value"] == 24:
            amount = self.Amount().decode(SSS)
        else:
            amount = self.Amount().decode(SSS[1:3])

        # Return data
        return { "amount": amount, "duration": duration }
    def _encode(self, data, **kwargs):
        return "{SSS}".format(
            SSS = self.Amount().encode(data["amount"] if "amount" in data else None,
                duration = data["duration"] if "duration" in data else None
            )
        )
    class Amount(pymetdecoder.Observation):
        _CODE = "SSS"
        _DESCRIPTION = "amount of sunshine"
        _CODE_LEN = 3
        _UNIT = "h"
        def _encode(self, data, **kwargs):
            duration = kwargs.get("duration")
            output = []
            if duration["value"] == 1:
                self._CODE_LEN = 2
                output = ["3"] # ensures it outputs 553xx
            output.append(self._encode_value(data))
            return "".join(output)
        def _decode_convert(self, val):
            return val / 10
        def _encode_convert(self, val):
            return int(val * 10)
class _CloudDriftDirection(pymetdecoder.Observation):
    """
    Direction of cloud drift

    * 56DDD - Direction of cloud drift
    """
    _CODE = "DDD"
    _DESCRIPTION = "direction of cloud drift"
    _CODE_LEN = 3
    def _decode(self, group):
        DL = group[2]
        DM = group[3]
        DH = group[4]
        attrs = ["low", "middle", "high"]

        output = {}
        for idx, d in enumerate([DL, DM, DH]):
            output[attrs[idx]] = self.Direction().decode(d)
        return output
    def _encode(self, data, **kwargs):
        return "{DL}{DM}{DH}".format(
            DL = self.Direction().encode(data["low"] if "low" in data else None, allow_none=True),
            DM = self.Direction().encode(data["middle"] if "middle" in data else None, allow_none=True),
            DH = self.Direction().encode(data["high"] if "high" in data else None, allow_none=True)
        )
    class Direction(pymetdecoder.Observation):
        _CODE = "D"
        _DESCRIPTION = "direction of cloud drift"
        _CODE_LEN = 1
        _CODE_TABLE = ct._CodeTable0700
class _CloudElevation(pymetdecoder.Observation):
    """
    Direction and elevation of cloud

    * 57CDe - direction and elevation of cloud
    """
    _CODE = "CDe"
    _DESCRIPTION = "direction and elevation of cloud"
    _CODE_LEN = 3
    def _decode(self, group):
        # Get values
        C = group[2]
        D = group[3]
        e = group[4]

        # Return data
        return {
            "genus": self.CloudGenus().decode(C),
            "direction": self.Direction().decode(D),
            "elevation": self.Elevation().decode(e)
        }
    def _encode(self, data, **kwargs):
        return "{C}{D}{e}".format(
            C = self.CloudGenus().encode(data["genus"] if "genus" in data else None),
            D = self.Direction().encode(data["direction"] if "direction" in data else None),
            e = self.Elevation().encode(data["elevation"] if "elevation" in data else None, allow_none=True)
        )
    class CloudGenus(pymetdecoder.Observation):
        _CODE = "C"
        _DESCRIPTION = "cloud genus"
        _CODE_LEN = 1
        _CODE_TABLE = ct._CodeTable0500
    class Direction(pymetdecoder.Observation):
        _CODE = "D"
        _DESCRIPTION = "direction of cloud"
        _CODE_LEN = 1
        _CODE_TABLE = ct._CodeTable0700
    class Elevation(pymetdecoder.Observation):
        _CODE = "e"
        _DESCRIPTION = "elevation of cloud"
        _CODE_LEN = 1
        _CODE_TABLE = ct._CodeTable1004
class _PressureChange(pymetdecoder.Observation):
    """
    Change of surface pressure over the last 24 hours

    * 5[89]ppp - Change of surface pressure
    """
    _CODE = "5[89]ppp"
    _DESCRIPTION = "change of surface pressure over the last 24 hours"
    _CODE_LEN = 3
    def _decode(self, group):
        # Get sign and change
        s   = group[1]
        ppp = group[2:5]

        # Return value
        return self.Change().decode(ppp, sign=s)
    def _encode(self, data, **kwargs):
        return "{sppp}".format(
            sppp = self.Change().encode(data)
        )
    class Change(pymetdecoder.Observation):
        _CODE = "ppp"
        _DESCRIPTION = "change of surface pressure over the last 24 hours"
        _CODE_LEN = 3
        _UNIT = "hPa"
        def _decode(self, raw, **kwargs):
            sign = kwargs.get("sign")
            if sign not in ["8", "9"]:
                return None
            return self._decode_value(raw, sign=sign)
        def _decode_convert(self, val, **kwargs):
            factor = 10 if kwargs.get("sign") == "8" else -10
            return val / factor
        def _encode_convert(self, val, **kwargs):
            return "{}{:03d}".format(
                8 if val >= 0 else 9,
                int(abs(val * 10))
            )
class _Precipitation(pymetdecoder.Observation):
    """
    Precipitation

    * 7RRRR - Precipitation amount
    """
    _CODE = "RRRR"
    _DESCRIPTION = "precipitation amount"
    _CODE_LEN = 4
    def _decode(self, group):
        RRRR = group[1:5]
        return {
            "amount": self.Amount().decode(RRRR),
            "time_before_obs": { "value": 24, "unit": "h" }
        }
    def _encode(self, data, **kwargs):
        if "time_before_obs" in data:
            if data["time_before_obs"] == { "value": 24, "unit": "h" }:
                return self.Amount().encode(data["amount"], group="7")
        return section1._Precipitation().encode(data, group="6")
    class Amount(pymetdecoder.Observation):
        _CODE = "RRRR"
        _DESCRIPTION = "precipitation amount"
        _CODE_LEN = 4
        _UNIT = "mm"
        _CODE_TABLE = ct._CodeTable3590A
class _PrevailingWind(pymetdecoder.Observation):
    """
    Prevailing wind

    * 7D(ddd) - prevailing wind direction
    """
    _CODE = "D"
    _DESCRIPTION = "prevailing wind direction"
    _CODE_LEN = 1
    _CODE_TABLE = ct._CodeTable0700
class _CloudLayer(pymetdecoder.Observation):
    """
    Layers/masses of clouds

    * 8NChh - Cloud layer
    """
    _CODE = "NChh"
    _DESCRIPTION = "cloud layer"
    _CODE_LEN = 4
    def _decode(self, group):
        N = group[1]
        C = group[2]
        hh = group[3:5]

        return {
            "cloud_cover": self.CloudCover().decode(N),
            "cloud_genus": self.CloudGenus().decode(C),
            "cloud_height": self.Height().decode(hh)
        }
    def _encode(self, data, **kwargs):
        output = []
        for d in data:
            output.append("{g}{N}{C}{hh}".format(
                g  = kwargs.get("group", 8),
                N  = self.CloudCover().encode(d["cloud_cover"] if "cloud_cover" in d else None),
                C  = self.CloudGenus().encode(d["cloud_genus"] if "cloud_genus" in d else None),
                hh = self.Height().encode(d["cloud_height"] if "cloud_height" in d else None)
            ))
        # Ensure groups are in order
        output.sort()
        return " ".join(output)
    class CloudCover(pymetdecoder.Observation):
        _CODE = "N"
        _DESCRIPTION = "cloud cover"
        _CODE_LEN = 1
        _CODE_TABLE = ct._CodeTable2700
    class CloudGenus(pymetdecoder.Observation):
        _CODE = "C"
        _DESCRIPTION = "cloud genus"
        _CODE_LEN = 1
        _CODE_TABLE = ct._CodeTable0500
    class Height(pymetdecoder.Observation):
        _CODE = "hh"
        _DESCRIPTION = "cloud height"
        _CODE_LEN = 2
        _CODE_TABLE = ct._CodeTable1677
        _UNIT = "m"
class _TimeBeforeObs(pymetdecoder.Observation):
    """
    Time before observation

    907tt - Time before observation
    """
    _CODE = "907tt"
    _DESCRIPTION = "time before observation"
    _CODE_LEN = 2
    _CODE_TABLE = ct._CodeTable4077
class _PrecipitationTime(pymetdecoder.Observation):
    """
    Time at which precipitation given by RRR began or ended and duration and
    character of precipitation

    909Rd - Time and character of precipitation
    """
    _CODE = "909Rd"
    _DESCRIPTION = "time and character of precipitation"
    _CODE_LEN = 2
    def _decode(self, group):
        # Get values
        R = group[3]
        d = group[4]

        # Decode and return
        return {
            "time": self.Time().decode(R),
            "character": self.Character().decode(d)
        }
    def _encode(self, data, **kwargs):
        return "909{R}{d}".format(
            R = self.Time().encode(data["time"] if "time" in data else None),
            d = self.Time().encode(data["character"] if "character" in data else None)
        )
    class Time(pymetdecoder.Observation):
        _CODE = "R"
        _DESCRIPTION = "begin or end time of precipitation"
        _CODE_LEN = 1
        _CODE_TABLE = ct._CodeTable3552
    class Character(pymetdecoder.Observation):
        _CODE = "d"
        _DESCRIPTION = "character of precipitation"
        _CODE_LEN = 1
        _CODE_TABLE = ct._CodeTable0833
class _HighestGust(pymetdecoder.Observation):
    """
    Highest gust

    * 91[01]ff - highest gust
    """
    _CODE = "91[01]ff"
    _DESCRIPTION = "highest gust"
    _CODE_LEN = 2
    def _decode(self, group, **kwargs):
        # Get type, speed and direction
        groups = group.split(" ")
        t  = groups[0][2]
        ff = groups[0][3:5]
        dd = None if len(groups) == 1 else groups[1][3:5]

        # Return values
        time_before = kwargs.get("time_before")
        measure_period = kwargs.get("measure_period")
        data = {
            "speed": self.Gust().decode(ff, unit=kwargs.get("unit")),
            "direction": self.Direction().decode(dd)
        }
        if time_before is not None:
            data["time_before_obs"] = time_before
        if measure_period is not None:
            data["measure_period"] = measure_period
        return data
    def _encode(self, data, **kwargs):
        time_before = kwargs.get("time_before")
        measure_period = kwargs.get("measure_period")
        output = []

        for d in data:
            # Convert time before obs, if required
            if "time_before_obs" in d:
                if time_before is None or (time_before is not None and d["time_before_obs"] != time_before):
                    tt = _TimeBeforeObs().encode(d["time_before_obs"])
                    if tt != "//":
                        output.append("907{}".format(tt))
                prefix = "911"
            elif "measure_period" in d:
                if d["measure_period"] == { "value": 10, "unit": "min" }:
                    prefix = "910"
                else:
                    raise pymetdecoder.EncodeError("Invalid value for measure_period")

            # Convert the gust
            ff = self.Gust().encode(d["speed"] if "speed" in d else None)
            output.append("{}{}".format(prefix, ff))

            # Convert the direction
            if "direction" in d and d["direction"] is not None:
                output.append("915{dd}".format(
                    dd = self.Direction().encode(d["direction"])
                ))

        # Return the codes
        return " ".join(output)
    class Gust(pymetdecoder.Observation):
        _CODE = "ff"
        _DESCRIPTION = "highest gust"
        _CODE_LEN = 2
    class Direction(pymetdecoder.Observation):
        _CODE = "dd"
        _DESCRIPTION = "gust direction"
        _CODE_LEN = 2
        _CODE_TABLE = ct._CodeTable0877
        _UNIT = "deg"
class _MeanWind(pymetdecoder.Observation):
    """
    Mean wind (highest/mean/lowest)

    * 91[234]ff - mean wind
    """
    _CODE = "91[234]ff"
    _DESCRIPTION = "mean wind"
    _CODE_LEN = 2
    def _encode(self, data, **kwargs):
        output = []
        if "highest" in data:
            output.append("912{ff}".format(
                ff = self._encode_value(data["highest"])
            ))
        return " ".join(output)
class _SnowFall(pymetdecoder.Observation):
    """
    Snow fall

    * 931ss - depth of newly fallen snow
    """
    _CODE = "931ss"
    _DESCRIPTION = "depth of newly fallen snow"
    _CODE_LEN = 2
    def _decode(self, group, **kwargs):
        # Get depth
        ss = group[3:5]

        # Return values
        time_before = kwargs.get("time_before")
        data = { "amount": self.Amount().decode(ss) }
        if time_before is not None:
            data["time_before_obs"] = time_before
        return data
    def _encode(self, data, **kwargs):
        return "931{ss}".format(
            ss = self.Amount().encode(data["amount"] if "amount" in data else None)
        )
    class Amount(pymetdecoder.Observation):
        _CODE = "931ss"
        _DESCRIPTION = "depth of newly fallen snow"
        _CODE_LEN = 2
        _CODE_TABLE = ct._CodeTable3870


# class _RadiationObs(pymetdecoder.Observation):
#     def convertUnit(self):
#         """
#         Since hourly radiation is in kJ/m2 and daily radiation is in J/cm2,
#         convert to the same unit - namely J/m2
#         """
#         try:
#             if self.amount.unit == "kJ/m2":
#                 self.amount.value *= 1000
#             elif self.amount.unit == "J/cm2":
#                 self.amount.value *= (100 * 100)
#             else:
#                 raise pymetdecoder.DecodeError("Unable to convert radiation units from {} to J/m2".format(self.amount.unit))
#             self.amount.setUnit("J/m2")
#         except Exception as e:
#             raise pymetdecoder.DecodeError("Unable to convert radiation units from {} to J/m2".format(self.amount.unit))

################################################################################
# OBSERVATION FUNCTIONS
################################################################################
def _ground_state(group):
    """
    Ground state without snow or measurable ice cover

    * 3EsTT - Ground state and temperature of ground
    """
    obs = pymetdecoder.Observation(group, noValAttr=True)
    try:
        # Get state and temperature
        E  = group[1:2]
        s  = group[2:3]
        TT = group[3:5]

        # Set the values
        obs.state       = pymetdecoder.Observation(raw=E, value=ct.checkRange(E, "0901", max=9))
        obs.temperature = pymetdecoder.Observation(group[2:5], unit="Cel")
        if obs.temperature.available:
            if s not in ["0", "1"]:
                logging.warning("{} is not a valid temperature sign code for code table 3845".format(s))
            else:
                obs.temperature.setValue(int(TT) * (1 if int(s) == "0" else -1))
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode ground state group {}".format(group))

    # Return the observation
    return obs
def _ground_state_snow(group):
    """
    Ground state with snow or measurable ice cover

    * 4Esss - Ground state and depth of snow
    """
    obs = pymetdecoder.Observation(group, noValAttr=True)
    try:
        # Get state and temperature
        E   = group[1:2]
        sss = group[2:5]

        # Set the values
        obs.state     = pymetdecoder.Observation(E, value=ct.checkRange(E, "0975", max=9))
        obs.snowDepth = pymetdecoder.Observation(sss, unit="cm")
        if obs.snowDepth.available:
            depth, quantifier, continuous, impossible = ct.codeTable3889(int(sss))
            obs.snowDepth.setValue(depth)
            obs.snowDepth.quantifier = quantifier
            obs.snowDepth.continuous = continuous
            obs.snowDepth.impossible = impossible
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode ground state snow group {}".format(group))

    # Return the observation
    return obs
def _evapotranspiration(group):
    """
    Daily amount of evaporation or evapotranspiration

    * 5EEEi -Amount of evaporation or evapotranspiration
    """
    obs = pymetdecoder.Observation(group, noValAttr=True)
    try:
        # Set availability
        if not obs.isAvailable(value=group[1:5]):
            obs.available = False

        # Set values
        if obs.available:
            # Get values
            EEE = group[1:4]
            obs.evaporation = pymetdecoder.Observation(EEE, value=int(EEE) / 10.0, unit="mm")

            i = group[4:5]
            (evapo, evapoTrans) = ct.codeTable1806(int(i))
            obs.instrument  = pymetdecoder.Observation(i, value=int(i))
            obs.instrument.evaporation = evapo
            obs.instrument.evapotranspiration = evapoTrans
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode evapotranspiration group {}".format(group))

    # Return the observation
    return obs
def _sunshine(group):
    """
    Amount of sunshine

    * 55SSS - Amount of sunshine
    """
    obs = pymetdecoder.Observation(group, noValAttr=True)
    try:
        # Set availability
        SSS = group[2:5]
        if not obs.isAvailable(value=SSS):
            obs.available = False

        # Set values
        if obs.available:
            if SSS[0:1] in ["0", "1", "2"]:
                obs.setValue(int(SSS) / 10)
                obs.setUnit("h")
                obs.duration = "24h"
            elif SSS[0:1] == "3":
                obs.setValue(int(SSS[1:2]) / 10)
                obs.setUnit("h")
                obs.duration = "1h"
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode sunshine group {}".format(group))

    # Return the observation
    return obs
def _radiation(group):
    """
    Amount and type of radiation

    * jFFFF - Type and amount of solar radiation
    """
    obs = _RadiationObs(group, noValAttr=True)
    try:
        # Get values
        j    = group[0:1]
        FFFF = group[1:5]

        # Set values
        obs.type   = pymetdecoder.Observation(j, value=int(j))
        obs.amount = pymetdecoder.Observation(FFFF, value=int(FFFF))
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode radiation group {}".format(group))

    # Return the observation
    return obs
def _cloud_drift_direction(group):
    """
    Direction of cloud drift

    * 56DDD - Direction of cloud drift
    """
    obs = pymetdecoder.Observation(group, noValAttr=True)
    try:
        DL = group[2:3]
        DM = group[3:4]
        DH = group[4:5]

        attrs = ["lowCloudDriftDirection", "middleCloudDriftDirection", "highCloudDriftDirection"]
        for i, d in enumerate([DL, DM, DH]):
            # Pass the value through the code table
            (dir, stationary, all) = ct.codeTable0700(d)
            dir_obs = pymetdecoder.Observation(d, value=dir)
            dir_obs.stationary = stationary
            dir_obs.allDirections = all
            setattr(obs, attrs[i], dir_obs)
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode cloud drift direction group {}".format(group))

    # Return the observation
    return obs
def _cloud_direction_elevation(group):
    """
    Direction and elevation of cloud

    * 57CDe - Direction and elevation of cloud
    """
    obs = pymetdecoder.Observation(group, noValAttr=True)
    try:
        C = group[2:3]
        D = group[3:4]
        e = group[4:5]

        # Get cloud type
        (cloud_val, cloud_avail) = ct.codeTable0500(C)
        obs.cloudType = pymetdecoder.Observation(C, value=cloud_val)

        # Get cloud direction
        (dir, stationary, all) = ct.codeTable0700(D)
        obs.direction = pymetdecoder.Observation(D, value=dir)
        obs.direction.stationary = stationary
        obs.direction.allDirections = all

        # Get elevation angle
        (angle, quantifier, visible) = ct.codeTable1004(int(e))
        obs.angle = pymetdecoder.Observation(e, value=angle)
        obs.angle.quantifier = quantifier
        obs.angle.visible = visible
    except Exception as e:
        raise pymetdecoder.DecodeError("Unable to decode cloud direction and elevation group {}".format(group))

    # Return the observation
    return obs
def _pressure_change(group):
    """
    Change of surface pressure over last 24 hours

    * 58ppp - Positive or zero change in pressure
    * 59ppp - Negative change in pressure
    """
    obs = pymetdecoder.Observation(group)
    try:
        # Set availability
        g = group[1:2]
        ppp = group[2:5]
        if not obs.isAvailable(value=ppp):
            obs.available = False

        # Get value
        if obs.available:
            if g == "8":
                value = int(ppp) * 0.1
            elif g == "9":
                value = int(ppp) * -0.1
            else:
                raise pymetdecoder.DecodeError("{} is an invalid value for surface pressure group".format(g))
            obs.setValue(value)
            obs.setUnit("hPa")
    except Exception as e:
        print(str(e))
        raise pymetdecoder.DecodeError("Unable to decode cloud direction and elevation group {}".format(group))

    # Return the observation
    return obs
