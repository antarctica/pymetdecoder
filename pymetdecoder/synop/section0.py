################################################################################
# pymetdecoder/synop/section0.py
#
# Decoder routines for section 0 of a SYNOP message
#
# TDBA 2019-01-21:
#   * First version
################################################################################
# CONFIGURATION
################################################################################
import re, types, pymetdecoder
from . import code_tables as ct
################################################################################
# OBSERVATION CLASSES
################################################################################
class _StationType(pymetdecoder.Observation):
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
class _Callsign(pymetdecoder.Observation):
    """
    Callsign

    * D...D - Ship's callsign consisting of three or more alphanumeric characters
    * A1bwnnn - WMO regional association area
    """
    def _decode(self, callsign):
        if re.match("^(1[1-7]|2[1-6]|3[1-4]|4[1-8]|5[1-6]|6[1-6]|7[1-4])\d{3}$", callsign):
            return {
                "region": ct._CodeTable0161().decode(callsign[0:2]),
                "value":  callsign
            }
        elif re.match("^[A-Z\d]{3,}", callsign):
            return { "value": callsign }
        else:
            raise pymetdecoder.InvalidCode(callsign, "callsign")
    def _encode(self, data):
        return data["value"]
class _ObservationTime(pymetdecoder.Observation):
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
    class Day(pymetdecoder.Observation):
        _CODE = "YY"
        _DESCRIPTION = "day of observation"
        _CODE_LEN = 2
        _VALID_RANGE = (1, 31)
    class Hour(pymetdecoder.Observation):
        _CODE = "GG"
        _DESCRIPTION = "hour of observation"
        _CODE_LEN = 2
        _VALID_RANGE = (0, 24)
class _WindIndicator(pymetdecoder.Observation):
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
        # # Check indicator is valid
        # self.is_valid(str(data["value"]), name="wind indicator (iw)")
        #
        # # Return value
        # return pymetdecoder.encode_attribute(data, None, 1)
class _StationID(pymetdecoder.Observation):
    """
    Station ID
    """
    def _decode(self, id):
        return { "value": id }
    def _encode(self, data):
        if data is not None:
            return data["value"]
        else:
            raise pymetdecoder.DecodeError("Cannot encode station ID: no value specified")
class _Region(pymetdecoder.Observation):
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
class _StationPosition(pymetdecoder.Observation):
    """
    Station position

    * 99LaLaLa QcLoLoLoLo - Latitude, globe quadrant and longitude
    * MMMULaULo h0h0h0h0im - Mobile land station position
    """
    def _decode(self, raw):
        # Check we have a valid number of raw groups
        if len(raw.split()) not in [2, 4]:
            raise pymetdecoder.DecodeError("Invalid groups for decoding station position ({})".format(raw))

        # Check if values are available
        available = False if re.match("^99/// /////", raw) else True # put in self.is_available?

        # Initialise data
        data = {}

        # Get values
        LaLaLa   = raw[2:5]  # Latitude
        Qc       = raw[6:7]  # Quadrant
        LoLoLoLo = raw[7:11] # Longitude

        # Set values
        data["latitude"]  = self.Latitude().decode(LaLaLa, quadrant=Qc)
        data["longitude"] = self.Longitude().decode(LoLoLoLo, quadrant=Qc)

        # The following is only for OOXX stations (MMMULaULo h0h0h0h0im)
        if len(raw.split()) == 4:
            MMM      = raw[12:15] # Marsden square
            ULa      = raw[15:16] # Latitude unit
            ULo      = raw[16:17] # Longitude unit
            h0h0h0h0 = raw[18:22] # Elevation
            im       = raw[22:23] # Elevation indicator/confidence

            # Check latitude unit digit and longitude unit digit match expected values
            if LaLaLa[-2] != ULa:
                raise pymetdecoder.DecodeError("Latitude unit digit does not match expected value ({} != {})".format(str(LaLaLa)[-2], ULa))
            if LoLoLoLo[-2] != ULo:
                raise pymetdecoder.DecodeError("Longitude unit digit does not match expected value ({} != {})".format(str(LoLoLoLo)[-2], ULo))

            # Decode values
            data["marsden_square"] = self.MarsdenSquare().decode(MMM)
            data["elevation"] = self.Elevation().decode(h0h0h0h0, unit="m" if int(im) < 4 else "ft")
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
    class Latitude(pymetdecoder.Observation):
        _CODE = "LaLaLa"
        _DESCRIPTION = "latitude"
        def _decode(self, raw, **kwargs):
            quadrant = kwargs.get("quadrant")
            return "{:.1f}".format(int(raw) / (-10.0 if quadrant in ["3", "5"] else 10.0))
        def _encode(self, data, **kwargs):
            quadrant = kwargs.get("quadrant")
            return int(float(data) * (-10.0 if quadrant in ["3", "5"] else 10.0))
    class Longitude(pymetdecoder.Observation):
        _CODE = "LoLoLoLo"
        _DESCRIPTION = "longitude"
        def _decode(self, raw, **kwargs):
            quadrant = kwargs.get("quadrant")
            return "{:.1f}".format(int(raw) / (-10.0 if quadrant in ["5", "7"] else 10.0))
        def _encode(self, data, **kwargs):
            quadrant = kwargs.get("quadrant")
            return int(float(data) * (-10.0 if quadrant in ["5", "7"] else 10.0))
    class MarsdenSquare(pymetdecoder.Observation):
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
    class Elevation(pymetdecoder.Observation):
        _CODE = "h0h0h0h0"
        _DESCRIPTION = "elevation"
        _CODE_LEN = 4
        def _decode(self, raw, **kwargs):
            unit = kwargs.get("unit")
            return self._decode_value(raw, unit=unit)
        def _encode(self, data):
            return self._encode_value(data)
    class Confidence(pymetdecoder.Observation):
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
                raise pymetdecoder.EncodeError("No units specified for elevation")
            if elevation["unit"] not in ["m", "ft"]:
                raise pymetdecoder.EncodeError("{} is not a valid unit for elevation".format(elevation["unit"]))

            return "{:1d}".format(confidence + (0 if elevation["unit"] == "m" else 4))
################################################################################
# OBSERVATION FUNCTIONS
################################################################################
# def _station_type(MMMM):
#     """
#     Station Type
#
#     * MMMM - station type
#     """
#     # Set the value
#     if re.match("^(AA|BB|OO)XX$", MMMM):
#         return { "value": MMMM }
#     else:
#         raise pymetdecoder.DecodeError("{} is an invalid station type".format(MMMM))
#
#     # obs = pymetdecoder.Observation(MMMM)
#     #
#     # # Set the value
#     # if re.match("^(AA|BB|OO)XX$", MMMM):
#     #     obs.setValue(MMMM)
#     #     return obs
#     # else:
#     #     raise pymetdecoder.DecodeError("{} is an invalid station type".format(MMMM))
# def _region(raw):
#     """
#     Region (I - VI, Antarctic or SHIP)
#     """
#     obs = pymetdecoder.Observation(raw)
#
#     # Region codes as determined by Manual On Codes Section D
#     regions = {
#         "I": [
#             [60000, 69998],
#         ],
#         "II": [
#             [20000, 20099], [20200, 21998], [23001, 25998], [28001, 32998],
#             [35001, 36998], [38001, 39998], [40350, 48599], [48800, 49998],
#             [50001, 59998]
#         ],
#         "III": [
#             [80001, 88998]
#         ],
#         "IV": [
#             [70001, 79998]
#         ],
#         "V": [
#             [48600, 48799], [90001, 98998]
#         ],
#         "VI": [
#             [1, 19998], [20100, 20199], [22001, 22998], [26001, 27998],
#             [33001, 34998], [37001, 37998], [40001, 40349]
#         ],
#         "Antarctic": [
#             [89001, 89998]
#         ]
#     }
#     for r in regions:
#         for region in regions[r]:
#             if region[0] <= int(raw) <= region[1]:
#                 obs.setValue(r)
#                 return obs
#     logging.warning("Unable to determine region from {}".format(self.raw))
# def _callsign(callsign):
#     """
#     Callsign
#
#     * D...D - Ship's callsign consisting of three or more alphanumeric characters
#     * A1bwnnn - WMO regional association area
#     """
#     obs = pymetdecoder.Observation(callsign)
#
#     # Set the values
#     if re.match("^(1[1-7]|2[1-6]|3[1-4]|4[1-8]|5[1-6]|6[1-6]|7[1-4])\d{3}$", callsign):
#         obs.region = pymetdecoder.Observation(callsign[0:2], value=ct.codeTable0161(callsign[0:2]))
#         obs.setValue(callsign)
#         # obs.id = callsign
#     elif re.match("^[A-Z\d]{3,}", callsign):
#         obs.setValue(callsign)
#     else:
#         raise pymetdecoder.DecodeError("Unable to determine callsign information from {}".format(self.raw))
#
#     # Return the observation
#     return obs
# def _observation_time(YYGG):
#     """
#     Observation time
#
#     * YYGG - day and hour of observation
#     """
#     obs = pymetdecoder.Observation(YYGG)
#
#     # Get the values
#     YY = YYGG[0:2]
#     GG = YYGG[2:4]
#
#     # Check observation time values are valid
#     if int(YY) > 31:
#         raise pymetdecoder.DecodeError("{} is an invalid value for observation day (YY)".format(YY))
#     if int(GG) > 24:
#         raise pymetdecoder.DecodeError("{} is an invalid value for observation hour (GG)".format(GG))
#
#     # Set the values
#     obs.day  = pymetdecoder.Observation(YY, value=int(YY))
#     obs.hour = pymetdecoder.Observation(GG, value=int(GG))
#
#     # Return the observation
#     return obs
# def _wind_indicator(iw):
#     """
#     Wind indicator
#
#     * iw - Indicator for source and units of wind speed
#     """
#     obs = pymetdecoder.Observation(iw)
#
#     # Check indicator is valid
#     if not re.match("[0134/]$", iw):
#         raise pymetdecoder.DecodeError("{} is an invalid value for the wind indicator (iw)".format(iw))
#
#     # Set the values
#     if obs.available:
#         obs.setValue(int(iw))
#         obs.setUnit("m/s" if obs.value < 2 else "KT")
#         obs.estimated = True if obs.value in [0, 3] else False
#
#     # Return the observation
#     return obs
# def _station_position(raw):
#     """
#     Station position
#
#     * 99LaLaLa QcLoLoLoLo - Latitude, globe quadrant and longitude
#     * MMMULaULo h0h0h0h0im - Mobile land station position
#     """
#     obs = _StationPositionObs(raw)
#
#     # Check we have a valid number of raw groups
#     if len(raw.split()) not in [2, 4]:
#         raise pymetdecoder.DecodeError("Invalid groups for decoding station position ({})".format(raw))
#
#     # Set the values
#     LaLaLa    = raw[2:5] # latitude
#     Qc        = raw[6:7] # quadrant
#     LoLoLoLo  = raw[7:11] # longitude
#     latitude  = "{:.1f}".format(int(LaLaLa) / (-10.0 if Qc in ["3", "5"] else 10.0)) if obs.available else LaLaLa
#     longitude = "{:.1f}".format(int(LoLoLoLo) / (-10.0 if Qc in ["5", "7"] else 10.0)) if obs.available else LoLoLoLo
#     obs.latitude  = pymetdecoder.Observation(LaLaLa)
#     obs.longitude = pymetdecoder.Observation(LoLoLoLo)
#     if obs.latitude.available:
#         obs.latitude.setValue(float(latitude))
#     if obs.longitude.available:
#         obs.longitude.setValue(float(longitude))
#
#     # The following is only for OOXX stations (MMMULaULo h0h0h0h0im)
#     if len(raw.split()) == 4:
#         MMM      = raw[12:15] # Marsden square
#         ULa      = raw[15:16] # Latitude unit
#         ULo      = raw[16:17] # Longitude unit
#         h0h0h0h0 = raw[18:22] # Elevation
#         im       = raw[22:23] # Elevation indicator/confidence
#         if (not 1 <= int(MMM) <= 623) and (not 901 <= int(MMM) <= 936):
#             raise pymetdecoder.DecodeError("{} is not a valid Marsden Square".format(MMM))
#         if LaLaLa[-2] != ULa:
#             raise pymetdecoder.DecodeError("Latitude unit digit does not match expected value ({} != {})".format(str(LaLaLa)[-2], ULa))
#         if LoLoLoLo[-2] != ULo:
#             raise pymetdecoder.DecodeError("Longitude unit digit does not match expected value ({} != {})".format(str(LoLoLoLo)[-2], ULo))
#
#         confidence = ["Poor", "Excellent", "Good", "Fair"]
#         obs.marsdenSquare = pymetdecoder.Observation(MMM, value=int(MMM))
#         obs.elevation = pymetdecoder.Observation(h0h0h0h0,
#             value = int(h0h0h0h0),
#             unit  = "m" if int(im) <= 4 else "ft"
#         )
#         obs.confidence = pymetdecoder.Observation(im, value=confidence[int(im) % 4])
#
#     # Return the observation
#     return obs
