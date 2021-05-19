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
from pymetdecoder import Observation, logging, DecodeError, EncodeError
from pymetdecoder import code_tables as ct
################################################################################
# SHARED CLASSES
################################################################################
class SimpleCodeTable(Observation):
    _CODE_TABLE = ct.CodeTableSimple
    _VALID_RANGE = (0, 9) # default valid range
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
        if str(sign) not in ["0", "1"]:
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

    * (iRixh)VV - Horizontal visibility at surface
    """
    _CODE = "VV"
    _DESCRIPTION = "horizontal visibility at surface"
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
        elif re.match("^[A-Z\d]{3,}", callsign):
            return { "value": callsign }
        else:
            raise pymetdecoder.InvalidCode(callsign, "callsign")
    def _encode(self, data):
        return data["value"]
class CloudDriftDirection(Observation):
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
    class Direction(DirectionCardinal):
        _DESCRIPTION = "direction of cloud drift"
class CloudElevation(Observation):
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
            "genus": CloudGenus().decode(C),
            "direction": self.Direction().decode(D),
            "elevation": self.Elevation().decode(e)
        }
    def _encode(self, data, **kwargs):
        return "{C}{D}{e}".format(
            C = CloudGenus().encode(data["genus"] if "genus" in data else None),
            D = self.Direction().encode(data["direction"] if "direction" in data else None, allow_none=True),
            e = self.Elevation().encode(data["elevation"] if "elevation" in data else None, allow_none=True)
        )
    class Direction(DirectionCardinal):
        _DESCRIPTION = "direction of cloud"
    class Elevation(Observation):
        _CODE = "e"
        _DESCRIPTION = "elevation of cloud"
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable1004
class CloudEvolution(Observation):
    """
    Evolution of clouds

    * 940Cn - evolution of clouds
    """
    _CODE = "940Cn"
    _DESCRIPTION = "evolution of clouds"
    _CODE_LEN = 2
    def _decode(self, group):
        # Get values
        C = group[3]
        n = group[4]

        # Return data
        return {
            "genus": CloudGenus().decode(C),
            "evolution": self.Evolution().decode(n)
        }
    def _encode(self, data, **kwargs):
        return "{C}{n}".format(
            C = CloudGenus().encode(data["genus"] if "genus" in data else None),
            n = self.Evolution().encode(data["evolution"] if "evolution" in data else None)
        )
    class Evolution(Observation):
        _CODE = "n"
        _DESCRIPTION = "cloud evolution"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 9)
class CloudLayer(Observation):
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
            "cloud_genus": CloudGenus().decode(C),
            "cloud_height": self.Height().decode(hh)
        }
    def _encode(self, data, **kwargs):
        output = []
        for d in data:
            output.append("{g}{N}{C}{hh}".format(
                g  = kwargs.get("group", 8),
                N  = self.CloudCover().encode(d["cloud_cover"] if "cloud_cover" in d else None),
                C  = CloudGenus().encode(d["cloud_genus"] if "cloud_genus" in d else None),
                hh = self.Height().encode(d["cloud_height"] if "cloud_height" in d else None)
            ))
        return " ".join(output)
    class CloudCover(CloudCover):
        _DESCRIPTION = "cloud cover"
    class Height(Observation):
        _CODE = "hh"
        _DESCRIPTION = "cloud height"
        _CODE_LEN = 2
        _CODE_TABLE = ct.CodeTable1677
        _UNIT = "m"
class CloudType(Observation):
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
    class CloudType(Observation):
        _CODE = "C"
        _DESCRIPTION = "cloud type"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 9)
    class CloudCover(Observation):
        _CODE = "N"
        _DESCRIPTION = "cloud cover"
        _CODE_LEN = 1
        _UNIT = "okta"
class CondensationTrails(Observation):
    """
    Condensation trails

    * 992Nt - condensation trails
    """
    _CODE_LEN = 2
    def _decode(self, group):
        N = group[3]
        t = group[4]
        return {
            "trail": self.Trail().decode(N),
            "time": self.Time().decode(t)
        }
    def _encode(self, data, **kwargs):
        return "{N}{t}".format(
            N = self.Trail().encode(data["trail"] if "trail" in data else None),
            t = self.Time().encode(data["time"] if "time" in data else None)
        )
    class Trail(Observation):
        _CODE = "N"
        _DESCRIPTION = "condensation trail"
        _CODE_LEN = 1
        _VALID_RANGE = (5, 9)
    class Time(SimpleCodeTable):
        # TODO: do this as an actual value
        _CODE = "t"
        _DESCRIPTION = "time of commencement of a phenomenon before the hour of observation"
        _CODE_LEN = 1
class DayDarkness(Observation):
    """
    Day darkness

    * 994AD - day darkness
    """
    _CODE_LEN = 2
    def _decode(self, group):
        A = group[3]
        D = group[4]
        return {
            "darkness": self.Darkness().decode(A),
            "direction": DirectionCardinal().decode(D)
        }
    def _encode(self, data, **kwargs):
        return "{A}{D}".format(
            A = self.Darkness().encode(data["darkness"] if "darkness" in data else None),
            D = DirectionCardinal().encode(data["direction"] if "direction" in data else None)
        )
    class Darkness(Observation):
        _CODE = "A"
        _DESCRIPTION = "Day darkness"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 2)
class DepositDiameter(Observation):
    """
    Diameter of deposit

    93[34567]RR - diameter of deposit
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

    * 929Ss - Drift snow
    """
    _CODE_LEN = 2
    def _decode(self, group):
        S = group[3]
        s = group[4]

        return {
            "phenomena": self.Phenomena().decode(S),
            "evolution": self.Evolution().decode(s)
        }
    def _encode(self, data, **kwargs):
        return "{S}{s}".format(
            S = self.Phenomena().encode(data["phenomena"] if "phenomena" in data else None),
            s = self.Evolution().encode(data["evolution"] if "evolution" in data else None)
        )
    class Phenomena(SimpleCodeTable):
        _CODE_LEN = 1
        _TABLE = "3766"
    class Evolution(SimpleCodeTable):
        _CODE_LEN = 1
        _TABLE = "3776"
        _VALID_RANGE = (0, 7)
class ExactObservationTime(Observation):
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
    class Hour(Hour):
        _DESCRIPTION = "hour of observation"
    class Minute(Minute):
        _DESCRIPTION = "minute of observation"
class Evapotranspiration(Observation):
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
    class Amount(Observation):
        _CODE = "EEE"
        _DESCRIPTION = "amount of evaporation or evapotranspiration"
        _CODE_LEN = 3
        _UNIT = "mm"
        def _decode_convert(self, val):
            return val / 10
        def _encode_convert(self, val):
            return int(val * 10)
    class TransType(Observation):
        _CODE = "i"
        _DESCRIPTION = "evaporation type"
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable1806
class FrozenDeposit(Observation):
    """
    Frozen deposit

    * 927ST - frozen deposit
    """
    _CODE_LEN = 2
    def _decode(self, group):
        S = group[3]
        T = group[4]

        return {
            "deposit": self.Deposit().decode(S),
            "variation": self.Variation().decode(T)
        }
    def _encode(self, data, **kwargs):
        return "{S}{T}".format(
            S = self.Deposit().encode(data["deposit"] if "deposit" in data else None),
            T = self.Variation().encode(data["variation"] if "variation" in data else None)
        )
    class Deposit(SimpleCodeTable):
        _CODE_LEN = 1
        _TABLE = "3764"
        _VALID_RANGE = (0, 7)
    class Variation(SimpleCodeTable):
        _CODE_LEN = 1
        _TABLE = "3955"
class Geopotential(Observation):
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

    * 0TT(RR) - Ground (grass) minimum temperature of the preceding night, in whole degrees Celsius
    """
    _CODE = "TT"
    _DESCRIPTION = "Ground (grass) minimum temperature of the preceding night"
    _CODE_LEN = 2
    _UNIT = "Cel"
    def _decode_convert(self, val, **kwargs):
        if 0 <= int(val) <= 49:
            return int(val)
        elif 50 <= int(val) <= 99:
            return 50 - int(val)
        # return (int(val) / 10) + (0 if int(val) > 500 else 1000)
    def _encode_convert(self, val, **kwargs):
        if val < 0:
            return val + 50
        else:
            return val
class GroundState(Observation):
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
    class State(Observation):
        _CODE = "E"
        _DESCRIPTION = "state of the ground without snow or measurable ice cover"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 9)
    class Temperature(Observation):
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
class GroundStateSnow(Observation):
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
    class State(Observation):
        _CODE = "E"
        _DESCRIPTION = "state of the ground with snow or measurable ice cover"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 9)
    class Depth(Observation):
        _CODE = "sss"
        _DESCRIPTION = "depth of snow"
        _CODE_LEN = 3
        _CODE_TABLE = ct.CodeTable3889
        _UNIT = "cm"
class HighestGust(Observation):
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
                    dd = self.Direction().encode(d["direction"])
                ))

        # Return the codes
        return " ".join(output)
    class Gust(Observation):
        _CODE = "ff"
        _DESCRIPTION = "highest gust"
        _CODE_LEN = 2
    class Direction(DirectionDegrees):
        _DESCRIPTION = "gust direction"
class IceAccretion(Observation):
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
    class Source(Observation):
        _CODE = "I"
        _DESCRIPTION = "ice accretion source"
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable1751
    class Thickness(Observation):
        _CODE = "EE"
        _DESCRIPTION = "ice accretion thickness"
        _CODE_LEN = 2
        _UNIT = "cm"
    class Rate(Observation):
        _CODE = "R"
        _DESCRIPTION = "ice accretion rate"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 4)
class LocalPrecipitation(Observation):
    """
    Precipitation character and time of precipitation for Region I

    * 0(TT)RR - precipitation character and time of precipitation
    """
    _CODE = "RR"
    _DESCRIPTION = "precipitation character and time of precipitation"
    _CODE_LEN = 2
    def _decode(self, group):
        return {
            "character": self.Character().decode(group[0]),
            "time": self.Time().decode(group[1])
        }
    def _encode(self, data, **kwargs):
        return "{RC}{Rt}".format(
            RC = self.Character().encode(data["character"] if "character" in data else None),
            Rt = self.Time().encode(data["time"] if "time" in data else None)
        )
    class Character(SimpleCodeTable):
        _CODE = "R"
        _CODE_LEN = 1
        _DESCRIPTION = "character and intensity of precipitation"
    class Time(SimpleCodeTable):
        _CODE = "R"
        _CODE_LEN = 1
        _DESCRIPTION = "time of beginning or end of precipitation"
class LowestCloudBase(Observation):
    """
    Lowest cloud base

    * (iRix)h(VV) - Height above surface of the base of the lowest cloud
    """
    _CODE = "h"
    _DESCRIPTION = "height above surface of the base of the lowest cloud"
    _CODE_LEN = 1
    _CODE_TABLE = ct.CodeTable1600
    _UNIT = "m"
class MaxLowCloudConcentration(Observation):
    """
    Location of maximum concentration of low-level clouds

    * 940Cn - evolution of clouds
    """
    _CODE = "944CD"
    _DESCRIPTION = "location of maximum concentration of low-level clouds"
    _CODE_LEN = 2
    def _decode(self, group):
        # Get values
        C = group[3]
        D = group[4]

        # Return data
        return {
            "cloud_type": self.CloudType().decode(C),
            "direction": DirectionCardinal().decode(D)
        }
    def _encode(self, data, **kwargs):
        return "{C}{D}".format(
            C = self.CloudType().encode(data["cloud_type"] if "cloud_type" in data else None),
            D = DirectionCardinal().encode(data["direction"] if "direction" in data else None, allow_none=True)
        )
    class CloudType(Observation):
        _CODE = "C"
        _DESCRIPTION = "cloud type"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 9)
class Mirage(Observation):
    """
    Mirage

    * 991AD - Mirage
    """
    _CODE = "991AD"
    _DESCRIPTION = "mirage"
    _CODE_LEN = 2
    def _decode(self, group):
        # Get values
        A = group[3]
        D = group[4]

        # Return data
        return {
            "mirage_type": self.MirageType().decode(A),
            "direction": DirectionCardinal().decode(D)
        }
    def _encode(self, data, **kwargs):
        return "{A}{D}".format(
            A = self.MirageType().encode(data["mirage_type"] if "mirage_type" in data else None),
            D = DirectionCardinal().encode(data["direction"] if "direction" in data else None, allow_none=True)
        )
    class MirageType(Observation):
        _CODE = "A"
        _DESCRIPTION = "mirage type"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 8)
class MountainCondition(Observation):
    """
    Cloud conditions over mountains and passes

    * 950Nn - cloud conditions over mountains and passes
    """
    _CODE = "950Nn"
    _DESCRIPTION = "cloud conditions over mountains and passes"
    _CODE_LEN = 2
    def _decode(self, group):
        # Get codes
        N = group[3]
        n = group[4]

        # Decode and return
        return {
            "conditions": self.Condition().decode(N),
            "evolution": self.Evolution().decode(n)
        }
    def _encode(self, data, **kwargs):
        return  "{N}{n}".format(
            N = self.Condition().encode(data["conditions"] if "conditions" in data else None),
            n = self.Evolution().encode(data["evolution"] if "evolution" in data else None)
        )
    class Condition(Observation):
        _CODE = "N"
        _DESCRIPTION = "cloud conditions over mountains and passes"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 9)
    class Evolution(Observation):
        _CODE = "n"
        _DESCRIPTION = "cloud evolution"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 9)
class ObservationTime(Observation):
    """
    Observation time

    * YYGG - day and hour of observation
    """
    _CODE = "YYGG"
    _DESCRIPTION = "day and hour of observation"
    def _decode(self, YYGG):
        # Get the values
        YY = YYGG[0:2]
        GG = YYGG[2:4]

        # Return values
        return { "day": self.Day().decode(YY), "hour": self.Hour().decode(GG) }
    def _encode(self, data):
        return "{YY}{GG}".format(
            YY = self.Day().encode(data["day"] if "day" in data else None),
            GG = self.Hour().encode(data["hour"] if "hour" in data else None)
        )
    class Day(Day):
        _DESCRIPTION = "day of observation"
    class Hour(Hour):
        _DESCRIPTION = "hour of observation"
class OpticalPhenomena(Observation):
    """
    Optical phenomena
    """
    _CODE = "990Zi"
    _DESCRIPTION = "optical phenomena"
    def _decode(self, group):
        # Get the values
        Z = group[3]
        i = group[4]

        # Return values
        return {
            "phenomena": self.Phenomena().decode(Z),
            "intensity": self.Intensity().decode(i)
        }
    def _encode(self, data, **kwargs):
        return "{Z}{i}".format(
            Z = self.Phenomena().encode(data["phenomena"] if "phenomena" in data else None),
            i = self.Intensity().encode(data["intensity"] if "intensity" in data else None)
        )
    class Phenomena(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable5161
    class Intensity(Observation):
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable1861
class Precipitation(Observation):
    """
    Precipitation

    * 6RRRt - Precipitation amount
    """
    _CODE = "RRRt"
    _DESCRIPTION = "precipitation amount"
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
        _CODE = "RRR"
        _DESCRIPTION = "precipitation amount"
        _CODE_LEN = 3
        _CODE_TABLE = ct.CodeTable3590
        _UNIT = "mm"
    class Amount24(Observation):
        _CODE = "RRRR"
        _DESCRIPTION = "precipitation amount"
        _CODE_LEN = 4
        _CODE_TABLE = ct.CodeTable3590A
        _UNIT = "mm"
    class TimeBeforeObs(Observation):
        _CODE = "t"
        _DESCRIPTION = "time before precipitation observation"
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable4019
        _UNIT = "h"
class PrecipitationIndicator(Observation):
    """
    Precipitation indicator

    * iR(ixhVV) - Precipitation indicator
    """
    _CODE = "iR"
    _DESCRIPTION = "precipitation indicator"
    _CODE_LEN = 1
    _VALID_RANGE = (0, 4)
    def _decode(self, iR, **kwargs):
        # TODO: codes 6 - 8 are valid if station is Russian
        return {
            "value": int(iR),
            "in_group_1": True if iR in ["0", "1", "6"] else False,
            "in_group_3": True if iR in ["0", "2", "7"] else False
        }
    def _encode(self, data):
        # todo: include autodetect i.e:
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
            return False
        except Exception:
            return False
class PrecipitationTime(Observation):
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
    class Time(Observation):
        _CODE = "R"
        _DESCRIPTION = "begin or end time of precipitation"
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable3552
    class Character(Observation):
        _CODE = "d"
        _DESCRIPTION = "character of precipitation"
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable0833
class Pressure(Observation):
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
class PressureChange(Observation):
    """
    Change of surface pressure over the last 24 hours

    * 5[89]ppp - Change of surface pressure
    """
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
    class Tendency(Observation):
        _CODE = "a"
        _DESCRIPTION = "pressure tendency indicator"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 8)
    class Change(Observation):
        _CODE = "ppp"
        _DESCRIPTION = "pressure tendency change"
        _CODE_LEN = 3
        _UNIT = "hPa"
        def _decode_convert(self, val, **kwargs):
            tendency = kwargs.get("tendency")
            return (val / (10.0 if tendency["value"] < 5 else -10.0))
        def _encode_convert(self, val, **kwargs):
            return abs(val * 10)
class PrevailingWind(DirectionCardinal):
    """
    Prevailing wind

    * 7D(ddd) - prevailing wind direction
    """
class Radiation(Observation):
    """
    Radiation

    jFFFF - radiation
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
        raise pymetdecoder.InvalidCode(raw, "region")
class RelativeHumidity(Observation):
    """
    Relative humidity

    * 29UUU - relative humidity
    """
    _CODE = "UUU"
    _DESCRIPTION = "relative humidity"
    _CODE_LEN = 3
    _VALID_RANGE = (0, 100)
    _UNIT = "%"
class SeaLandIce(Observation):
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
    class Concentration(Observation):
        _CODE = "c"
        _DESCRIPTION = "concentration or arrangment of sea ice"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 9)
    class Development(Observation):
        _CODE = "S"
        _DESCRIPTION = "stage of development"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 9)
    class LandOrigin(Observation):
        _CODE = "b"
        _DESCRIPTION = "ice of land origin"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 9)
    class Direction(Observation):
        _CODE = "D"
        _DESCRIPTION = "bearing of ice edge"
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable0739
    class ConditionTrend(Observation):
        _CODE = "z"
        _DESCRIPTION = "present ice situation and trend of conditions over preceding three hours"
        _CODE_LEN = 1
        _VALID_RANGE = (0, 9)
class SeaSurfaceTemperature(Observation):
    """
    Sea surface temperature

    * 0sTTT - Sea surface temperature and its type of measurement
    """
    _CODE = "sTTT"
    _DESCRIPTION = "sea surface temperature and its type of measurement"
    _CODE_LEN = 4
    def _decode(self, group):
        # Get the values
        s   = group[1]
        TTT = group[2:5]

        # Get sign and measurement type
        m_type = self.MeasurementType().decode(s)

        # Return temperature and measurement type
        # itemp = self.Temperature().decode(TTT, sign=)
        if m_type is None:
            return None
        else:
            sign = 0 if int(m_type["_code"]) % 2 == 0 else 1
            temp = self.Temperature().decode(TTT, sign=sign)
            if temp is None:
                temp = { "value": None }
            temp["measurement_type"] = m_type
            return temp
    def _encode(self, data, **kwargs):
        return "{s}{TTT}".format(
            s   = self.MeasurementType().encode(data["measurement_type"]),
            TTT = self.Temperature().encode(data, allow_none=True)[1:]
        )
    class MeasurementType(Observation):
        _CODE = "s"
        _DESCRIPTION = "sea surface temperature measurement type"
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable3850
    class Temperature(SignedTemperature):
        _DESCRIPTION = "sea surface temperature"
class SeaState(SimpleCodeTable):
    """
    State of the sea

    * 924S(V) - state of the sea
    """
    _CODE_LEN = 1
    _TABLE = "3700"
class SeaVisibility(Observation):
    """
    State of the sea

    * 924(S)V - Visibility seawards (from a coastal station)
    """
    _CODE_LEN = 1
    _CODE_TABLE = ct.CodeTable4300
    _UNIT = "m"
class ShipDisplacement(Observation):
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
    class Direction(DirectionCardinal):
        _DESCRIPTION = "direction of displacement of the ship since 3 hours"
    class Speed(Observation):
        _CODE = "v"
        _DESCRIPTION = "speed of displacement of the ship since 3 hours"
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable4451
class SnowCoverRegularity(Observation):
    """
    Character and regularity of snow cover

    * 928Ss - Character and regularity of snow cover
    """
    _CODE_LEN = 2
    def _decode(self, group):
        S = group[3]
        s = group[4]

        return {
            "cover": self.Cover().decode(S),
            "regularity": self.Regularity().decode(s)
        }
    def _encode(self, data, **kwargs):
        return "{S}{s}".format(
            S = self.Cover().encode(data["cover"] if "cover" in data else None),
            s = self.Regularity().encode(data["regularity"] if "regularity" in data else None)
        )
    class Cover(SimpleCodeTable):
        _CODE_LEN = 1
        _TABLE = "3765"
        _VALID_RANGE = (0, 8)
    class Regularity(SimpleCodeTable):
        _CODE_LEN = 1
        _TABLE = "3775"
        _VALID_RANGE = (0, 8)
class SnowFall(Observation):
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
    class Amount(Observation):
        _CODE = "931ss"
        _DESCRIPTION = "depth of newly fallen snow"
        _CODE_LEN = 2
        _CODE_TABLE = ct.CodeTable3870
class SpecialClouds(Observation):
    """
    Special clouds

    * 993CD - Special clouds
    """
    _CODE_LEN = 2
    def _decode(self, group):
        C = group[3]
        D = group[4]

        return {
            "cloud_type": self.CloudType().decode(C),
            "direction": self.Direction().decode(D)
        }
    def _encode(self, data, **kwargs):
        return "{C}{d}".format(
            C = self.CloudType().encode(data["cloud_type"] if "cloud_type" in data else None),
            d = self.Direction().encode(data["direction"] if "direction" in data else None, allow_none=True)
        )
    class CloudType(SimpleCodeTable):
        _CODE_LEN = 1
        _TABLE = "0521"
        _VALID_RANGE = (1, 5)
    class Direction(DirectionCardinal):
        _DESCRIPTION = "true direction in which orographic clouds or clouds with vertical development are seen"
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

    * 99LLL QLLLL - Latitude, globe quadrant and longitude
    * MMMUU hhhhi - Mobile land station position
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
        _CODE = "LaLaLa"
        _DESCRIPTION = "latitude"
        def _decode(self, raw, **kwargs):
            quadrant = kwargs.get("quadrant")
            return "{:.1f}".format(int(raw) / (-10.0 if quadrant in ["3", "5"] else 10.0))
        def _encode(self, data, **kwargs):
            quadrant = kwargs.get("quadrant")
            return int(float(data) * (-10.0 if quadrant in ["3", "5"] else 10.0))
    class Longitude(Observation):
        _CODE = "LoLoLoLo"
        _DESCRIPTION = "longitude"
        def _decode(self, raw, **kwargs):
            quadrant = kwargs.get("quadrant")
            return "{:.1f}".format(int(raw) / (-10.0 if quadrant in ["5", "7"] else 10.0))
        def _encode(self, data, **kwargs):
            quadrant = kwargs.get("quadrant")
            return int(float(data) * (-10.0 if quadrant in ["5", "7"] else 10.0))
    class MarsdenSquare(Observation):
        _CODE = "MMM"
        _DESCRIPTION = "Marsden square"
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
        _CODE = "h0h0h0h0"
        _DESCRIPTION = "elevation"
        _CODE_LEN = 4
        def _decode(self, raw, **kwargs):
            unit = kwargs.get("unit")
            return self._decode_value(raw, unit=unit)
        def _encode(self, data):
            return self._encode_value(data)
    class Confidence(Observation):
        _CODE = "im"
        _DESCRIPTION = "confidence"
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

    * 99[89]UU - sudden rise/fall in relative humidity
    """
    _CODE = "9[89]UU"
    _DESCRIPTION = "sudden rise/fall in relative humidity"
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

    * 99[67]TT - sudden rise/fall in air temperature
    """
    _CODE = "9[67]TT"
    _DESCRIPTION = "sudden rise/fall in air temperature"
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
        if direction is not None and direction["calm"] and speed is not None and speed["value"] > 0:
            logging.warning("Wind is calm, yet has a speed (dd: {}, ff: {})".format(dd, ff))
            speed = None

        return {
            "direction": direction,
            "speed": speed
        }
    def _encode(self, data, **kwargs):
        return "{dd}{ff}".format(
            dd = self.Direction().encode(data["direction"] if "direction" in data else None, allow_none=True),
            ff = self.Speed().encode(data["speed"] if "speed" in data else None)
        )
    class Direction(DirectionDegrees):
        _DESCRIPTION = "surface wind direction"
    class Speed(Observation):
        _CODE = "ff"
        _DESCRIPTION = "surface wind speed"
        _CODE_LEN = 2
        def encode(self, data, **kwargs):
            if data is not None and data["value"] > 99:
                return "99 00{}".format(self._encode_value(data))
            else:
                return self._encode_value(data)
class Sunshine(Observation):
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
class SwellWaves(Observation):
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
        _CODE = "dd"
        _DESCRIPTION = "direction of swell waves"
        _CODE_LEN = 2
        _CODE_TABLE = ct.CodeTable0877
        _UNIT = "deg"
    class Period(Observation):
        _CODE = "PP"
        _DESCRIPTION = "period of swell waves"
        _CODE_LEN = 2
        _UNIT = "s"
    class Height(Observation):
        _CODE = "HH"
        _DESCRIPTION = "height of swell waves"
        _CODE_LEN = 2
        _UNIT = "m"
        def _decode_convert(self, val, **kwargs):
            return int(val) * 0.5
        def _encode_convert(self, val, **kwargs):
            return int(val * 2)
class Temperature(Observation):
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
class TimeBeforeObs(Observation):
    """
    Time before observation

    907tt - Time before observation
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

    900zz - Variability, location or intensity
    """
    _CODE_LEN = 2
    _CODE_TABLE = ct.CodeTable4077Z
class ValleyClouds(Observation):
    """
    Fog, mist or low cloud in valleys or plains, observed from a station at a higher level

    951Nn - fog, mist or low cloud in valleys or plains, observed from a station at a higher level
    """
    _CODE_LEN = 2
    def _decode(self, group):
        N = group[3]
        n = group[4]
        return {
            "condition": self.Condition().decode(N),
            "evolution": self.Evolution().decode(n)
        }
    def _encode(self, data, **kwargs):
        return "{N}{n}".format(
            N = self.Condition().encode(data["condition"] if "condition" in data else None),
            n = self.Evolution().encode(data["evolution"] if "evolution" in data else None)
        )
    class Condition(SimpleCodeTable):
        _CODE_LEN = 1
        _TABLE = "2754"
    class Evolution(SimpleCodeTable):
        _CODE_LEN = 1
        _TABLE = "2864"
class VisibilityDirection(Observation):
    """
    Visiblity in a direction

    98xxx - Visibility in a direction
    """
    _CODE = "dVV"
    _DESCRIPTION = "visibility in a direction"
    _CODE_LEN = 3
    def _decode(self, group):
        # Get direction and visibility
        dir = group[2]
        vis = group[3:5]

        # If direction code is 9, it's variable visibility
        if dir == "9":
            logging.warning("989VV to be coded separately")
            return None

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
        return "{d}{VV}".format(
            d  = DirectionCardinal().encode(data["direction"] if "direction" in data else None),
            VV = Visibility().encode(data["visibility"] if "visibility" in data else None)
        )
class Weather(Observation):
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
            raise DecodeError("{} is not a valid weather type".format(weather_type))
class WeatherIndicator(Observation):
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
class WetBulbTemperature(Observation):
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
    class Status(Observation):
        _CODE = "s"
        _DESCRIPTION = "sign and type of wet bulb temperature"
        _CODE_LEN = 1
        _CODE_TABLE = ct.CodeTable3855
    class Temperature(Observation):
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
class WindIndicator(Observation):
    """
    Wind indicator

    * iw - Indicator for source and units of wind speed
    """
    _CODE = "iw"
    _DESCRIPTION = "indicator for source and units of wind speed"
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
    class Period(Observation):
        _CODE = "PP"
        _DESCRIPTION = "period of wind waves"
        _CODE_LEN = 2
        _UNIT = "s"
    class Height(Observation):
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
