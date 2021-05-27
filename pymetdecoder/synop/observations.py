################################################################################
# pymetdecoder/synop/observations.py
#
# Observation classes from SYNOP
#
# TDBA 2019-01-21:
#   * First version
# TDBA 2020-11-12:
#   * Merged from individual section scripts
################################################################################
# CONFIGURATION
################################################################################
import re
from pymetdecoder import Observation, logging, DecodeError, EncodeError, InvalidCode
from pymetdecoder import code_tables as ct
################################################################################
# SHARED CLASSES
################################################################################
class SimpleCodeTable(Observation):
    _CODE_TABLE = ct.CodeTableSimple
    _VALID_RANGE = (0, 9) # default valid range
    _CODE_LEN = 1
class CloudCover(Observation):
    """
    Cloud cover

    * N(ddff) - Total cloud cover
    """
    _CODE_LEN = 1
    _CODE_TABLE = ct.CodeTable2700
    _UNIT = "okta"
class CloudGenus(Observation):
    """
    Cloud genus
    """
    _CODE_LEN = 1
    _CODE_TABLE = ct.CodeTable0500
class Day(Observation):
    """
    Day of observation
    """
    _CODE_LEN = 2
    _VALID_RANGE = (1, 31)
class DirectionCardinal(Observation):
    """
    Cardinal direction
    """
    _CODE_LEN = 1
    _CODE_TABLE = ct.CodeTable0700
class DirectionDegrees(Observation):
    """
    Direction in degrees
    """
    _CODE_LEN = 2
    _CODE_TABLE = ct.CodeTable0877
    _UNIT = "deg"
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
class SignedTemperature(Observation):
    """
    Temperature with sign value
    """
    _CODE_LEN = 4
    _UNIT = "Cel"
    def _decode(self, raw, **kwargs):
        sign = kwargs.get("sign")
        if str(sign) == "/":
            return None
        if str(sign) not in ["0", "1"]:
            raise InvalidCode(sign, "temperature sign")
            return None
        return self._decode_value(raw, sign=sign)
    def _decode_convert(self, val, **kwargs):
        factor = 10 if str(kwargs.get("sign")) == "0" else -10
        return val / factor
    def _encode_convert(self, val, **kwargs):
        return "{}{:03d}".format(
            0 if val >= 0 else 1,
            int(abs(val * 10))
        )
class Visibility(Observation):
    """
    Visibility
    """
    _CODE_LEN = 2
    _CODE_TABLE = ct.CodeTable4377
    _UNIT = "m"
    def _encode(self, data, use90=None):
        if use90 is None:
            use90 = data["use90"] if "use90" in data else False
        return self._encode_value(data, use90=use90)
################################################################################
# OTHER CLASSES
################################################################################
class Callsign(Observation):
    """
    Callsign

    * D...D - Ship's callsign consisting of three or more alphanumeric characters
    * Abnnn - WMO regional association area
    """
    def _decode(self, callsign):
        if re.match("^(1[1-7]|2[1-6]|3[1-4]|4[1-8]|5[1-6]|6[1-6]|7[1-4])\d{3}$", callsign):
            return {
                "region": ct.CodeTable0161().decode(callsign[0:2]),
                "value":  callsign
            }
        elif re.match("^[A-Za-z\d]{3,}", callsign):
            return { "value": str(callsign).upper() }
        else:
            raise InvalidCode(callsign, "callsign")
    def _encode(self, data):
        return str(data["value"]).upper()
class CloudDriftDirection(Observation):
    """
    Direction of cloud drift
    """
    _CODE_LEN = 3
    _COMPONENTS = [
        ("low", 2, 1, DirectionCardinal),
        ("middle", 3, 1, DirectionCardinal),
        ("high", 4, 1, DirectionCardinal)
    ]
class CloudElevation(Observation):
    """
    Direction and elevation of cloud
    """
    _CODE_LEN = 3
    class Elevation(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable1004
    _COMPONENTS = [
        ("genus", 2, 1, CloudGenus),
        ("direction", 3, 1, DirectionCardinal),
        ("elevation", 4, 1, Elevation)
    ]
class CloudEvolution(Observation):
    """
    Evolution of clouds
    """
    _CODE_LEN = 2
    class Evolution(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable2863
    _COMPONENTS = [
        ("genus", 3, 1, CloudGenus),
        ("evolution", 4, 1, Evolution)
    ]
class CloudLayer(Observation):
    """
    Layers/masses of clouds
    """
    _CODE_LEN = 4
    def _decode(self, group):
        N = group[1]
        C = group[2]
        hh = group[3:5]

        return {
            "cloud_cover": CloudCover().decode(N),
            "cloud_genus": CloudGenus().decode(C),
            "cloud_height": self.Height().decode(hh)
        }
    def _encode(self, data, **kwargs):
        output = []
        for d in data:
            output.append("8{N}{C}{hh}".format(
                N  = CloudCover().encode(d["cloud_cover"] if "cloud_cover" in d else None),
                C  = CloudGenus().encode(d["cloud_genus"] if "cloud_genus" in d else None),
                hh = self.Height().encode(d["cloud_height"] if "cloud_height" in d else None)
            ))
        return " ".join(output)
    class Height(Observation):
        _CODE_LEN = 2
        _CODE_TABLE = ct.CodeTable1677
        _UNIT = "m"
class CloudType(Observation):
    """
    Cloud Types/Amount
    """
    _CODE_LEN = 4
    def _decode(self, group):
        # Get the components
        Nh = group[1:2] # Amount of lowest cloud if there is lowest cloud, else base of middle cloud
        CL = group[2:3] # Lowest cloud type
        CM = group[3:4] # Middle cloud type
        CH = group[4:5] # High cloud type

        # Initialise data dict
        data = {
            "low_cloud_type": self.LowCloud().decode(CL),
            "middle_cloud_type": self.MiddleCloud().decode(CM),
            "high_cloud_type": self.HighCloud().decode(CH)
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
            N =  self.CloudCover().encode(cloud_cover),
            CL = self.LowCloud().encode(data["low_cloud_type"] if "low_cloud_type" in data else None),
            CM = self.MiddleCloud().encode(data["middle_cloud_type"] if "middle_cloud_type" in data else None),
            CH = self.HighCloud().encode(data["high_cloud_type"] if "high_cloud_type" in data else None),
        )
    class CloudCover(Observation):
        _CODE_LEN = 1
        _UNIT = "okta"
    class LowCloud(SimpleCodeTable):
        _TABLE = "0513"
    class MiddleCloud(SimpleCodeTable):
        _TABLE = "0515"
    class HighCloud(SimpleCodeTable):
        _TABLE = "0509"
class CondensationTrails(Observation):
    """
    Condensation trails
    """
    _CODE_LEN = 2
    class Trail(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable2752
    class Time(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable4055
        _UNIT = "min"
    _COMPONENTS = [
        ("trail", 3, 1, Trail),
        ("time", 4, 1, Time)
    ]
class DayDarkness(Observation):
    """
    Day darkness
    """
    _CODE_LEN = 2
    class Darkness(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable0163
    _COMPONENTS = [
        ("darkness", 3, 1, Darkness),
        ("direction", 4, 1, DirectionCardinal)
    ]
class DepositDiameter(Observation):
    """
    Diameter of deposit
    """
    _TYPES = [None, None, None, "solid", "glaze", "rime", "compound", "wet_snow"]
    def _decode(self, group):
        t  = group[2]
        RR = group[3:5]
        output = {}
        diameter = self.Diameter().decode(RR)
        deposit = self._TYPES[int(t)]
        output[deposit] = diameter
        return output
    def _encode(self, data, **kwargs):
        for d in data:
            if d in self._TYPES:
                deposit = self._TYPES.index(d)
                break
        return "{d}{RR}".format(
            d  = deposit,
            RR = self.Diameter().encode(data[d])
        )
    class Diameter(Observation):
        _CODE_LEN = 2
        _CODE_TABLE = ct.CodeTable3570
        _UNIT = "mm"
class DriftSnow(Observation):
    """
    Drift snow
    """
    _CODE_LEN = 2
    class Phenomena(SimpleCodeTable):
        _TABLE = "3766"
    class Evolution(SimpleCodeTable):
        _TABLE = "3776"
        _VALID_RANGE = (0, 7)
    _COMPONENTS = [
        ("phenomena", 3, 1, Phenomena),
        ("evolution", 4, 1, Evolution)
    ]
class ExactObservationTime(Observation):
    """
    Exact observation time
    """
    _CODE_LEN = 4
    _COMPONENTS = [
        ("hour", 1, 2, Hour),
        ("minute", 3, 2, Minute)
    ]
class Evapotranspiration(Observation):
    """
    Daily amount of evaporation or evapotranspiration
    """
    _CODE_LEN = 4
    class Amount(Observation):
        _CODE_LEN = 3
        _UNIT = "mm"
        def _decode_convert(self, val):
            return val / 10
        def _encode_convert(self, val):
            return int(val * 10)
    class TransType(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable1806
    _COMPONENTS = [
        ("amount", 1, 3, Amount),
        ("type", 4, 1, TransType)
    ]
class FrozenDeposit(Observation):
    """
    Frozen deposit
    """
    _CODE_LEN = 2
    class Deposit(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable3764
    class Time(SimpleCodeTable):
        _TABLE = "3955"
    _COMPONENTS = [
        ("deposit", 3, 1, Deposit),
        ("variation", 4, 1, Time)
    ]
class Geopotential(Observation):
    """
    Geopotential
    """
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
    class Surface(Observation):
        _CODE = "a"
        _DESCRIPTION = "geopotential surface"
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable0264
    class Height(Observation):
        _CODE = "hhh"
        _DESCRIPTION = "geopotential height"
        _CODE_LEN = 3
        _UNIT = "gpm"
        def _decode_convert(self, val, **kwargs):
            surface = int(kwargs.get("surface"))
            if surface == 2:
                return val + (1000 if val < 300 else 0)
            if surface == 7:
                return val + (3000 if val < 500 else 2000)
            if surface == 8:
                return val + 1000
            return val
        def _encode_convert(self, val, **kwargs):
            surface = kwargs.get("surface")
            code = int(surface["_code"])
            if code == 2:
                return val - (1000 if val >= 1000 else 0)
            if code == 7:
                return val - (3000 if val >= 3000 else 2000)
            if code == 8:
                return val - 1000

            # Check value still valid (must be between 0 and 999)
            if 0 <= val <= 999:
                return val
            else:
                raise pymetdecode.EncodeError()
class GroundMinimumTemperature(Observation):
    """
    Ground (grass) minimum temperature of the preceding night, in whole degrees Celsius
    (Region I only)
    """
    _CODE_LEN = 2
    _UNIT = "Cel"
    def _decode_convert(self, val, **kwargs):
        if 0 <= int(val) <= 49:
            return int(val)
        elif 50 <= int(val) <= 99:
            return 50 - int(val)
    def _encode_convert(self, val, **kwargs):
        if val < 0:
            return val + 50
        else:
            return val
class GroundState(Observation):
    """
    Ground state without snow or measurable ice cover
    """
    _CODE_LEN = 4
    class State(SimpleCodeTable):
        _TABLE = "0901"
    class Temperature(Observation):
        _CODE_LEN = 3
        _UNIT = "Cel"
        def _decode(self, raw, **kwargs):
            sign = raw[0]
            if sign == "/":
                return None
            if sign not in ["0", "1"]:
                raise InvalidCode(sign, "temperature sign")
                return None
            return self._decode_value(raw[1:3], sign=sign)
        def _decode_convert(self, val, **kwargs):
            factor = 1 if kwargs.get("sign") == "0" else -1
            return val / factor
        def _encode_convert(self, val, **kwargs):
            return "{}{:02d}".format(
                0 if val >= 0 else 1,
                int(abs(val))
            )
    _COMPONENTS = [
        ("state", 1, 1, State),
        ("temperature", 2, 3, Temperature)
    ]
class GroundStateSnow(Observation):
    """
    Ground state with snow or measurable ice cover
    """
    _CODE_LEN = 4
    class State(SimpleCodeTable):
        _TABLE = "0975"
    class Depth(Observation):
        _CODE_LEN = 3
        _CODE_TABLE = ct.CodeTable3889
        _UNIT = "cm"
    _COMPONENTS = [
        ("state", 1, 1, State),
        ("depth", 2, 3, Depth)
    ]
class HighestGust(Observation):
    """
    Highest gust
    """
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
            "direction": DirectionDegrees().decode(dd)
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
                    tt = TimeBeforeObs().encode(d["time_before_obs"])
                    if tt != "//":
                        output.append("907{}".format(tt))
                prefix = "911"
            elif "measure_period" in d:
                if d["measure_period"] == { "value": 10, "unit": "min" }:
                    prefix = "910"
                else:
                    raise EncodeError("Invalid value for measure_period")

            # Convert the gust
            ff = self.Gust().encode(d["speed"] if "speed" in d else None)
            output.append("{}{}".format(prefix, ff))

            # Convert the direction
            if "direction" in d and d["direction"] is not None:
                output.append("915{dd}".format(
                    dd = DirectionDegrees().encode(d["direction"])
                ))

        # Return the codes
        return " ".join(output)
    class Gust(Observation):
        _CODE_LEN = 2
class IceAccretion(Observation):
    """
    Ice accretion
    """
    _CODE_LEN = 4
    class Source(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable1751
    class Thickness(Observation):
        _CODE_LEN = 2
        _UNIT = "cm"
    class Rate(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable3551
    _COMPONENTS = [
        ("source", 1, 1, Source),
        ("thickness", 2, 2, Thickness),
        ("rate", 4, 1, Rate)
    ]
class ImportantWeather(Observation):
    """
    Amplification of weather phenomenon
    """
    _CODE_LEN = 2
    def _decode(self, raw, **kwargs):
        use_4687 = kwargs.get("use_4687", False)
        if use_4687:
            self._CODE_TABLE = ct.CodeTable4687
        else:
            return { "value": int(raw), "_table": "4677" }
class LocalPrecipitation(Observation):
    """
    Precipitation character and time of precipitation for Region I
    """
    _CODE_LEN = 2
    class Character(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable167
    class Time(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable168
        _UNIT = "h"
    _COMPONENTS = [
        ("character", 0, 1, Character),
        ("time", 1, 1, Time)
    ]
class LocationMaxConcentration(Observation):
    """
    Location of maximum concentration of phenomenon
    """
    _CODE_LEN = 2
    class Elevation(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable0938
    _COMPONENTS = [
        ("elevation", 3, 1, Elevation),
        ("direction", 4, 1, DirectionCardinal)
    ]
class LowestCloudBase(Observation):
    """
    Lowest cloud base
    """
    _CODE_LEN = 1
    _CODE_TABLE = ct.CodeTable1600
    _UNIT = "m"
class MaxLowCloudConcentration(Observation):
    """
    Location of maximum concentration of low-level clouds
    """
    _CODE_LEN = 2
    class CloudType(SimpleCodeTable):
        _TABLE = "0513"
    _COMPONENTS = [
        ("cloud_type", 3, 1, CloudType),
        ("direction", 4, 1, DirectionCardinal)
    ]
class Mirage(Observation):
    """
    Mirage
    """
    _CODE_LEN = 2
    class MirageType(SimpleCodeTable):
        _TABLE = "0101"
    _COMPONENTS = [
        ("mirage_type", 3, 1, MirageType),
        ("direction", 4, 1, DirectionCardinal)
    ]
class MountainCondition(Observation):
    """
    Cloud conditions over mountains and passes
    """
    _CODE_LEN = 2
    class Condition(SimpleCodeTable):
        _TABLE = "2745"
    class Evolution(Observation):
        _CODE_TABLE = ct.CodeTable2863
        _CODE_LEN = 1
    _COMPONENTS = [
        ("conditions", 3, 1, Condition),
        ("evolution", 4, 1, Evolution)
    ]
class ObservationTime(Observation):
    """
    Observation time
    """
    _CODE_LEN = 4
    _COMPONENTS = [
        ("day", 0, 2, Day),
        ("hour", 2, 2, Hour)
    ]
class OpticalPhenomena(Observation):
    """
    Optical phenomena
    """
    class Phenomena(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable5161
    class Intensity(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable1861
    _COMPONENTS = [
        ("phenomena", 3, 1, Phenomena),
        ("intensity", 4, 1, Intensity)
    ]
class PhenomSpeedDir(Observation):
    """
    Forward speed and direction from which phenomenon is moving
    """
    _CODE_LEN = 2
    class Speed(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable4448
    _COMPONENTS = [
        ("speed", 3, 1, Speed),
        ("direction", 4, 1, DirectionCardinal)
    ]
class Precipitation(Observation):
    """
    Precipitation
    """
    _CODE_LEN = 4
    def _decode(self, group, **kwargs):
        # Check if we're getting tenths of mm
        tenths = kwargs.get("tenths", False)

        # Calculate amount
        if tenths:
            RRRR = group[1:5]
            return {
                "amount": self.Amount24().decode(RRRR),
                "time_before_obs": self.TimeBeforeObs().decode("4") # 4 represents 24 hours
            }
        else:
            RRR = group[1:4]
            t   = group[4:5]
            return {
                "amount": self.Amount().decode(RRR),
                "time_before_obs": self.TimeBeforeObs().decode(t)
            }
    def _encode(self, data, **kwargs):
        is_24h = kwargs.get("is_24h", False)
        if is_24h:
            return self.Amount24().encode(data["amount"] if "amount" in data else None)
        else:
            return "{RRR}{t}".format(
                RRR = self.Amount().encode(data["amount"] if "amount" in data else None),
                t = self.TimeBeforeObs().encode(data["time_before_obs"] if "time_before_obs" in data else None)
            )
    class Amount(Observation):
        _CODE_LEN = 3
        _CODE_TABLE = ct.CodeTable3590
        _UNIT = "mm"
    class Amount24(Observation):
        _CODE_LEN = 4
        _CODE_TABLE = ct.CodeTable3590A
        _UNIT = "mm"
    class TimeBeforeObs(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable4019
        _UNIT = "h"
class PrecipitationIndicator(Observation):
    """
    Precipitation indicator
    """
    _CODE_LEN = 1
    def _decode(self, i, **kwargs):
        country = kwargs.get("country")
        return {
            "value": int(i),
            "in_group_1": True if (i in ["0", "1"]) or (i == "6" and country == "RU") else False,
            "in_group_3": True if (i in ["0", "2"]) or (i == "7" and country == "RU") else False
        }
    def _encode(self, data):
        # TODO: include autodetect i.e.
        # 0 if precip in section 1 and 3
        # 1 if precip in section 1
        # 2 if precip in section 3
        # 3 if precip is not in either section, but 0
        # 4 if precip is not in either section and amount is not available
        # For RU stations and precip measured by automatic sensors:
        #   * 6 if precip in section 1
        #   * 7 if precip in section 3
        #   * 8 if precip is not in either section and amount is not available
        return str(data["value"])
    def _is_valid(self, val, **kwargs):
        try:
            if 0 <= float(val) <= 4:
                return True
            else:
                # Special case for Russian stations
                country = kwargs.get("country")
                if country == "RU" and val in ["6", "7", "8"]:
                    return True
        except Exception:
            return False
class PrecipitationTime(Observation):
    """
    Time at which precipitation given by RRR began or ended and duration and
    character of precipitation
    """
    _CODE_LEN = 2
    class Time(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable3552
    class Character(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable0833
    _COMPONENTS = [
        ("time", 3, 1, Time),
        ("character", 4, 1, Character)
    ]
class Pressure(Observation):
    """
    Pressure
    """
    _CODE_LEN = 4
    _UNIT = "hPa"
    def _decode_convert(self, val, **kwargs):
        return (int(val) / 10) + (0 if int(val) > 500 else 1000)
    def _encode_convert(self, val, **kwargs):
        return abs(val * 10) - (10000 if val >= 1000 else 0)
class PressureChange(Observation):
    """
    Change of surface pressure over the last 24 hours
    """
    _CODE_LEN = 4
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
    class Change(Observation):
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
class PressureTendency(Observation):
    """
    Pressure tendency
    """
    _CODE_LEN = 4
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
    class Tendency(SimpleCodeTable):
        _TABLE = "0200"
        _VALID_RANGE = (0, 8)
    class Change(Observation):
        _CODE_LEN = 3
        _UNIT = "hPa"
        def _decode_convert(self, val, **kwargs):
            tendency = kwargs.get("tendency")
            try:
                return (val / (10.0 if tendency["value"] < 5 else -10.0))
            except Exception:
                return None
        def _encode_convert(self, val, **kwargs):
            return abs(val * 10)
class Radiation(Observation):
    """
    Radiation
    """
    _CODE_LEN = 4
    def _decode(self, group, **kwargs):
        return {
            "value": int(group) if group.isnumeric() else None,
            "unit": kwargs.get("unit"),
            "time_before_obs": kwargs.get("time_before")
        }
    def _encode(self, data, **kwargs):
        return "{:04d}".format(data["value"])
    def is_available(self, value):
        return True
class Region(Observation):
    """
    Region (I - VI, Antarctic or SHIP)
    """
    def _decode(self, raw):
        # Region codes as determined by Manual On Codes Section D
        regions = {
            "I": [
                [60000, 69998],
            ],
            "II": [
                [20000, 20099], [20200, 21998], [23001, 25998], [28001, 32998],
                [35001, 36998], [38001, 39998], [40350, 48599], [48800, 49998],
                [50001, 59998]
            ],
            "III": [
                [80001, 88998]
            ],
            "IV": [
                [70001, 79998]
            ],
            "V": [
                [48600, 48799], [90001, 98998]
            ],
            "VI": [
                [1, 19998], [20100, 20199], [22001, 22998], [26001, 27998],
                [33001, 34998], [37001, 37998], [40001, 40349]
            ],
            "Antarctic": [
                [89001, 89998]
            ]
        }
        for r in regions:
            for region in regions[r]:
                if region[0] <= int(raw) <= region[1]:
                    return { "value": r }
        raise InvalidCode(raw, "region")
class RelativeHumidity(Observation):
    """
    Relative humidity
    """
    _CODE_LEN = 3
    _VALID_RANGE = (0, 100)
    _UNIT = "%"
class SeaLandIce(Observation):
    """
    Sea/land ice information
    """
    _CODE_LEN = 5
    _ENCODE_DEFAULT = "ICE /////"
    def _decode(self, group):
        # If we only have one item in the ice group, then we can't do anything
        if len(group) <= 1:
            return None

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
    class Concentration(SimpleCodeTable):
        _CODE_LEN = 1
        _TABLE = "0639"
    class Development(SimpleCodeTable):
        _CODE_LEN = 1
        _TABLE = "3739"
    class LandOrigin(SimpleCodeTable):
        _CODE_LEN = 1
        _TABLE = "0439"
    class Direction(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable0739
    class ConditionTrend(SimpleCodeTable):
        _CODE_LEN = 1
        _TABLE = "5239"
class SeaSurfaceTemperature(Observation):
    """
    Sea surface temperature
    """
    _CODE_LEN = 4
    def _decode(self, group):
        # Get the values
        s   = group[1]
        TTT = group[2:5]

        # Get sign and measurement type
        m_type = self.MeasurementType().decode(s)

        # Return temperature and measurement type
        if m_type is None:
            return None
        else:
            sign = 0 if int(m_type["_code"]) % 2 == 0 else 1
            temp = SignedTemperature().decode(TTT, sign=sign)
            if temp is None:
                temp = { "value": None }
            temp["measurement_type"] = m_type
            return temp
    def _encode(self, data, **kwargs):
        return "{s}{TTT}".format(
            s   = self.MeasurementType().encode(data["measurement_type"]),
            TTT = SignedTemperature().encode(data, allow_none=True)[1:]
        )
    class MeasurementType(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable3850
    class Temperature(SignedTemperature):
        _DESCRIPTION = "sea surface temperature"
class SeaState(Observation):
    """
    State of the sea
    """
    _CODE_LEN = 1
    _CODE_TABLE = ct.CodeTable3700
class SeaVisibility(Observation):
    """
    State of the sea
    """
    _CODE_LEN = 1
    _CODE_TABLE = ct.CodeTable4300
    _UNIT = "m"
class ShipDisplacement(Observation):
    """
    Ship displacement
    """
    _CODE_LEN = 2
    def _decode(self, group):
        D = group[3]
        v = group[4]

        # should 22200 be decoded? it represents a stationary sea station (12.3.1.2)
        if D == "0" and v == "0":
            return None

        return {
            "direction": DirectionCardinal().decode(D),
            "speed": self.Speed().decode(v)
        }
    def _encode(self, data, **kwargs):
        allow_none = kwargs.get("allow_none", False)
        if data is None and allow_none:
            return "00"
        else:
            return "{D}{v}".format(
                D = DirectionCardinal().encode(data["direction"] if "direction" in data else None, allow_none=True),
                v = self.Speed().encode(data["speed"] if "speed" in data else None)
            )
    class Speed(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable4451
class SnowCoverRegularity(Observation):
    """
    Character and regularity of snow cover
    """
    _CODE_LEN = 2
    class Cover(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable3765
    class Regularity(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable3775
    _COMPONENTS = [
        ("cover", 3, 1, Cover),
        ("regularity", 4, 1, Regularity)
    ]
class SnowFall(Observation):
    """
    Snow fall
    """
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
    class Amount(Observation):
        _CODE_LEN = 2
        _CODE_TABLE = ct.CodeTable3870
class SpecialClouds(Observation):
    """
    Special clouds
    """
    _CODE_LEN = 2
    class CloudType(SimpleCodeTable):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable0521
    _COMPONENTS = [
        ("cloud_type", 3, 1, CloudType),
        ("direction", 4, 1, DirectionCardinal)
    ]
class StationID(Observation):
    """
    Station ID
    """
    def _decode(self, id):
        return { "value": id }
    def _encode(self, data):
        if data is not None:
            return data["value"]
        else:
            raise DecodeError("Cannot encode station ID: no value specified")
class StationPosition(Observation):
    """
    Station position
    """
    def _decode(self, raw):
        # Check we have a valid number of raw groups
        if len(raw.split()) not in [2, 4]:
            raise DecodeError("Invalid groups for decoding station position ({})".format(raw))

        # Check if values are available
        available = False if re.match("^99/// /////", raw) else True # put in self.is_available?

        # Initialise data
        data = {}

        # Get values
        lat = raw[2:5]  # Latitude
        Q   = raw[6:7]  # Quadrant
        lon = raw[7:11] # Longitude

        # Check both values are numeric, otherwise we can't get the position
        try:
            int(lat)
            int(lon)
        except:
            raise InvalidCode(raw, "latitude/longitude")

        # Set values
        data["latitude"]  = self.Latitude().decode(lat, quadrant=Q)
        data["longitude"] = self.Longitude().decode(lon, quadrant=Q)

        # The following is only for OOXX stations (MMMULaULo h0h0h0h0im)
        if len(raw.split()) == 4:
            MMM  = raw[12:15] # Marsden square
            ULa  = raw[15:16] # Latitude unit
            ULo  = raw[16:17] # Longitude unit
            hhhh = raw[18:22] # Elevation
            im   = raw[22:23] # Elevation indicator/confidence

            # Check latitude unit digit and longitude unit digit match expected values
            if lat[-2] != ULa:
                logging.warning("Latitude unit digit does not match expected value ({} != {})".format(str(lat)[-2], ULa))
            if lon[-2] != ULo:
                logging.warning("Longitude unit digit does not match expected value ({} != {})".format(str(lon)[-2], ULo))

            # Decode values
            data["marsden_square"] = self.MarsdenSquare().decode(MMM)
            data["elevation"] = self.Elevation().decode(hhhh, unit="m" if int(im) < 4 else "ft")
            data["confidence"] = self.Confidence().decode(im)

        # Return data
        return data
    def _encode(self, data, **kwargs):
        obs_type = kwargs.get("obs_type")

        # If data is none, ensure we print out the correct number of groups
        if data is None:
            if obs_type == "BBXX":
                return "///// /////"
            elif obs_type == "OOXX":
                return "///// ///// ///// /////"
            else:
                raise EncodeError("{} is not a valid observation type")

        # Initialise groups
        groups = []

        # Work out the quadrant
        if float(data["latitude"]) < 0:
            if float(data["longitude"]) < 0:
                quadrant = "5"
            else:
                quadrant = "3"
        else:
            if float(data["longitude"]) < 0:
                quadrant = "7"
            else:
                quadrant = "1"

        # Encode latitude and longitude
        groups.append("99{lat}".format(
            lat = "{:03d}".format(self.Latitude().encode(data["latitude"] if "latitude" in data else None, quadrant=quadrant))
        ))
        groups.append("{quadrant}{lon}".format(
            lon = "{:04d}".format(self.Longitude().encode(data["longitude"] if "longitude" in data else None, quadrant=quadrant)),
            quadrant = quadrant
        ))

        # Encode additional information for OOXX
        if obs_type == "OOXX":
            groups.append("{MMM}{ULa}{ULo}".format(
                MMM = self.MarsdenSquare().encode(data["marsden_square"] if "marsden_square" in data else None),
                ULa = groups[0][-2],
                ULo = groups[1][-2]
            ))
            groups.append("{h0h0h0h0}{im}".format(
                h0h0h0h0 = self.Elevation().encode(data["elevation"] if "elevation" in data else None),
                im = self.Confidence().encode(data["confidence"] if "confidence" in data else None, elevation=data["elevation"])
            ))

        # Return the data
        return " ".join(groups)
    class Latitude(Observation):
        def _decode(self, raw, **kwargs):
            quadrant = kwargs.get("quadrant")
            return "{:.1f}".format(int(raw) / (-10.0 if quadrant in ["3", "5"] else 10.0))
        def _encode(self, data, **kwargs):
            quadrant = kwargs.get("quadrant")
            return int(float(data) * (-10.0 if quadrant in ["3", "5"] else 10.0))
    class Longitude(Observation):
        def _decode(self, raw, **kwargs):
            quadrant = kwargs.get("quadrant")
            return "{:.1f}".format(int(raw) / (-10.0 if quadrant in ["5", "7"] else 10.0))
        def _encode(self, data, **kwargs):
            quadrant = kwargs.get("quadrant")
            return int(float(data) * (-10.0 if quadrant in ["5", "7"] else 10.0))
    class MarsdenSquare(Observation):
        _CODE_LEN = 3
        def _decode(self, raw):
            return int(raw)
        def _encode(self, data):
            return int(data)
        def _is_valid(self, value):
            if (not 1 <= int(value) <= 623) and (not 901 <= int(value) <= 936):
                return False
            else:
                return True
    class Elevation(Observation):
        _CODE_LEN = 4
        def _decode(self, raw, **kwargs):
            unit = kwargs.get("unit")
            return self._decode_value(raw, unit=unit)
        def _encode(self, data):
            return self._encode_value(data)
    class Confidence(Observation):
        _CODE_LEN = 1
        _CONFIDENCE = ["Poor", "Excellent", "Good", "Fair"]
        def _decode(self, raw, **kwargs):
            return self._CONFIDENCE[int(raw) % 4]
        def _encode(self, data, **kwargs):
            elevation = kwargs.get("elevation")
            confidence = self._CONFIDENCE.index(data)
            if "unit" not in elevation:
                raise EncodeError("No units specified for elevation")
            if elevation["unit"] not in ["m", "ft"]:
                raise EncodeError("{} is not a valid unit for elevation".format(elevation["unit"]))

            return "{:1d}".format(confidence + (0 if elevation["unit"] == "m" else 4))
class StationType(Observation):
    """
    Station Type

    * MMMM - station type
    """
    _CODE = "MMMM"
    _DESCRIPTION = "station type"
    _VALID_REGEXP = "^(AA|BB|OO)XX$"
    def _decode(self, MMMM):
        if self.is_valid(MMMM):
            return { "value": MMMM }
    def _encode(self, data):
        if self.is_valid(data["value"]):
            return data["value"]
class SuddenHumidityChange(Observation):
    """
    Sudden rise/fall in relative humidity
    """
    _CODE_LEN = 2
    _UNIT = "%"
    def _decode_convert(self, val):
        sign = 1 if str(val).startswith("8") else -1
        val  = int(str(val)[1:3]) * sign
        return val
    def _encode_convert(self, data, **kwargs):
        return abs(data)
class SuddenTemperatureChange(Observation):
    """
    Sudden rise/fall in air temperature
    """
    _CODE_LEN = 2
    _UNIT = "Cel"
    def _decode_convert(self, val):
        sign = 1 if str(val).startswith("6") else -1
        val  = int(str(val)[1:3]) * sign
        return val
    def _encode_convert(self, data, **kwargs):
        return abs(data)
class SurfaceWind(Observation):
    """
    Surface wind
    """
    _CODE_LEN = 4
    def _decode(self, ddff):
        # Get direction and speed
        dd = ddff[0:2]
        ff = ddff[2:4]

        # Get direction and speed
        direction = DirectionDegrees().decode(dd)
        speed = self.Speed().decode(ff)

        # Perform sanity check - if the wind is calm, it can't have a speed
        if direction is not None and direction["calm"] and speed is not None and speed["value"] > 0:
            logging.warning("Wind is calm, yet has a speed (dd: {}, ff: {})".format(dd, ff))
            speed = None

        return {
            "direction": direction,
            "speed": speed
        }
    def _encode(self, data, **kwargs):
        return "{dd}{ff}".format(
            dd = DirectionDegrees().encode(data["direction"] if "direction" in data else None, allow_none=True),
            ff = self.Speed().encode(data["speed"] if "speed" in data else None)
        )
    class Speed(Observation):
        _CODE_LEN = 2
        def encode(self, data, **kwargs):
            if data is not None and data["value"] > 99:
                return "99 00{}".format(self._encode_value(data))
            else:
                return self._encode_value(data)
class Sunshine(Observation):
    """
    Amount of sunshine
    """
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
            raise DecodeError("{} is not a valid value for sunshine group duration".format(group[2]))

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
    class Amount(Observation):
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
class SwellWaves(Observation):
    """
    Swell waves
    """
    def _decode(self, group, **kwargs):
        # Split group into separate groups
        (dir_group, info_group) = group.split(" ")

        # Get direction
        if info_group.startswith("4"):
            dir = dir_group[1:3] if dir_group is not None else None
        elif info_group.startswith("5"):
            dir = dir_group[3:5] if dir_group is not None else None
        else:
            raise DecodeError("{} is not a valid swell wave group".format(g))
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
    class Direction(Observation):
        _CODE_LEN = 2
        _CODE_TABLE = ct.CodeTable0877
        _UNIT = "deg"
    class Period(Observation):
        _CODE_LEN = 2
        _UNIT = "s"
    class Height(Observation):
        _CODE_LEN = 2
        _UNIT = "m"
        def _decode_convert(self, val, **kwargs):
            return int(val) * 0.5
        def _encode_convert(self, val, **kwargs):
            return int(val * 2)
class Temperature(Observation):
    """
    Temperature observation
    """
    _CODE_LEN = 4
    def _decode(self, group):
        # Get the sign (sn) and temperature (TTT):
        sn  = group[1:2]
        TTT = group[2:5]

        # The last character can sometimes be a "/" instead of a 0, so fix
        TTT = re.sub("\/$", "0", TTT)

        # If sign is not 0 or 1, return None with log message
        if sn not in ["0", "1", "/"]:
            logging.warning("{} is an invalid temperature group".format(group))
            return None

        # Return value
        return SignedTemperature().decode(TTT, sign=sn)
    def _encode(self, data, group=None):
        return "{sTTT}".format(
            sTTT = SignedTemperature().encode(data)
        )
class TemperatureChange(Observation):
    """
    Temperature change
    """
    _CODE_LEN = 3
    class TimeBeforeObs(Observation):
        _CODE_LEN = 1
        _UNIT = "h"
        _VALID_RANGE = (0, 5)
    class Change(Observation):
        _CODE_LEN = 2
        _CODE_TABLE = ct.CodeTable0822
        _UNIT = "Cel"
    _COMPONENTS = [
        ("time_before_obs", 0, 1, TimeBeforeObs),
        ("change", 1, 2, Change)
    ]
class TimeBeforeObs(Observation):
    """
    Time before observation
    """
    _CODE_LEN = 2
    _CODE_TABLE = ct.CodeTable4077T
class TimeOfEnding(Observation):
    """
    Time of ending of weather phenomenon
    """
    _CODE_LEN = 2
    _CODE_TABLE = ct.CodeTable4077T
class VariableLocationIntensity(Observation):
    """
    Variability, location or intensity
    """
    _CODE_LEN = 2
    _CODE_TABLE = ct.CodeTable4077Z
class ValleyClouds(Observation):
    """
    Fog, mist or low cloud in valleys or plains, observed from a station at a higher level
    """
    _CODE_LEN = 2
    class Condition(SimpleCodeTable):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable2754
    class Evolution(SimpleCodeTable):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable2864
    _COMPONENTS = [
        ("condition", 3, 1, Condition),
        ("evolution", 4, 1, Evolution)
    ]
class VisibilityDirection(Observation):
    """
    Visiblity in a direction
    """
    _CODE_LEN = 3
    def _decode(self, group):
        # Get direction and visibility
        dir = group[2]
        vis = group[3:5]

        # Check if direction is valid
        if dir == "/":
            logging.warning(InvalidCode(dir, "visibility direction"))
            return None

        # If direction code is 9, it's variable visibility
        if dir == "9":
            direction = DirectionCardinal().decode(vis[0])["value"]
            if direction is None:
                direction = "towardsSea"
            return {
                "direction": { "value": direction },
                "variation": self.Variation().decode(vis[1])
            }

        # If direction code is 0, it's towards the sea
        direction = DirectionCardinal().decode(dir)["value"]
        if direction is None:
            direction = "towardsSea"

        # Return values
        return {
            "direction": { "value": direction },
            "visibility": Visibility().decode(vis)
        }
    def _encode(self, data, **kwargs):
        if "variation" in data:
            return "9{d}{V}".format(
                d = DirectionCardinal().encode(data["direction"] if "direction" in data else None),
                V = self.Variation().encode(data["variation"] if "variation" in data else None)
            )
        else:
            return "{d}{VV}".format(
                d  = DirectionCardinal().encode(data["direction"] if "direction" in data else None),
                VV = Visibility().encode(data["visibility"] if "visibility" in data else None)
            )
    class Variation(SimpleCodeTable):
        _TABLE = "4332"
class Weather(Observation):
    """
    Weather
    """
    _CODE_LEN = 2
    def _decode(self, group, **kwargs):
        time_before = kwargs.get("time_before")
        w_type = kwargs.get("type")
        if w_type == "present":
            table = "4677"
        elif w_type == "past":
            table = "4561"
        else:
            raise ValueError("{} is not a valid weather type".format(w_type))

        # If value is non-numeric, return None
        try:
            int(group)
        except Exception:
            return None

        # Initialise data
        data = { "value": int(group), "_table": table }
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
            raise DecodeError("{} is not a valid weather type".format(weather_type))
class WeatherIndicator(Observation):
    """
    Weather indicator
    """
    _CODE_LEN = 1
    _VALID_RANGE = (1, 7)
    def _decode(self, ix):
        return {
            "value": int(ix) if ix != "/" else None,
            "automatic": False if ix == "/" or int(ix) < 3 else True
        }
class WetBulbTemperature(Observation):
    """
    Wet bulb temperature
    """
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
        if temp is None or temp["value"] is None:
            return None
        else:
            temp.update(status)
        return temp
    def _encode(self, data, **kwargs):
        return "{s}{TTT}".format(
            s   = self.Status().encode(data),
            TTT = self.Temperature().encode(data)
        )
    class Status(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable3855
    class Temperature(Observation):
        _CODE_LEN = 3
        _UNIT = "Cel"
        def _decode(self, raw, **kwargs):
            sign = kwargs.get("sign")
            return self._decode_value(raw, sign=sign)
        def _decode_convert(self, val, **kwargs):
            sign = kwargs.get("sign")
            if sign is None:
                return None
            factor = 10 * sign
            return val / factor
        def _encode_convert(self, val, **kwargs):
            return abs(val * 10)
class WindIndicator(Observation):
    """
    Wind indicator
    """
    _CODE_LEN = 1
    _VALID_REGEXP = "[0134/]$"
    def _decode(self, iw):
        # Set the values
        return {
            "value": int(iw),
            "unit": "m/s" if int(iw) < 2 else "KT",
            "estimated": True if int(iw) in [0, 3] else False
        }
    def _encode(self, data):
        return self._encode_value(data)
class WindWaves(Observation):
    """
    Wind waves
    """
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
    class Period(Observation):
        _CODE_LEN = 2
        _UNIT = "s"
    class Height(Observation):
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
