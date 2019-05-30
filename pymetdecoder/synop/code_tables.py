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
import pymetdecoder, re, logging
################################################################################
# FUNCTIONS
################################################################################
def checkRange(x, table, min=0, max=0, nullChar="/"):
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
            return x
        elif min <= int(x) <= max:
            return int(x)
        else:
            logging.warning("{} is not a valid code for code table {}".format(x, table))
    except Exception as e:
        logging.warning("{} is not a valid code for code table {}".format(x, table))
################################################################################
# MAIN BODY
################################################################################
def codeTable0161(A1):
    """
    WMO Regional Association area in which buoy, drilling rig or oil- or gas-production
    platform has been deployed

    :param string A1: A1
    :returns: Region identifier (I, II etc)
    :rtype: string
    :raises: pymetdecoder.DecodeError if A1 is invalid
    """
    # Set region list
    regions = [None, "I", "II", "III", "IV", "V", "VI", "Antarctic"]

    # Check if given region is valid
    if re.match("(1[1-7]|2[1-6]|3[1-4]|4[1-8]|5[1-6]|6[1-6]|7[1-4])", A1):
        return regions[int(A1[0:1])]
    else:
        raise pymetdecoder.DecodeError("{} is not a valid code for code table 0161".format(A1))
def codeTable0264(a3):
    """
    Standard isobaric surface for which the geopotential is reported

    :param int a3: a3
    :returns: Geopotential surface in hPa
    :rtype: int
    :raises: pymetdecoder.DecodeError if a3 is invalid
    """
    surfaces = [None, 1000, 925, None, None, 500, None, 700, 850]
    if surfaces[a3] is None:
        raise pymetdecoder.DecodeError("{} is not a valid code for code table 0264".format(a3))
    else:
        return surfaces[a3]
def codeTable0700(D):
    """
    Direction or bearing in one figure

    :param string D: D
    :returns: Direction
    :rtype: string
    :returns: True if wind is calm or vessel is stationary, False otherwise (D = 0)
    :rtype: boolean
    :returns: True if direction is all directions, confused, variable or unknown, False otherwise (D = 9)
    :rtype: boolean
    """
    if D == "/":
        return (None, None, None)
    directions = ["", "NE", "E", "SE", "S", "SW", "W", "NW", "N", ""]
    isCalmOrStationary = False
    allDirections = False
    if int(D) == 0:
        isCalmOrStationary = True
    elif int(D) == 9:
        allDirections = True
    direction = directions[int(D)]
    return (direction, isCalmOrStationary, allDirections)
def codeTable0739(Di):
    """
    True bearing of principle ice edge

    :param string Di: Di
    :returns: Direction
    :rtype: string
    :returns: True if ship is in shore, False otherwise (Di == 0)
    :rtype: boolean
    :returns: True if ship is in ice, False otherwise (Di == 9)
    :rtype: boolean
    """
    try:
        if Di == "/":
            return (None, None, None)
        directions = [None, "NE", "E", "SE", "S", "SW", "W", "NW", "N", None]
        shipInShore = True if int(Di) == 0 else False
        shipInIce   = True if int(Di) == 9 else False
        direction   = directions[int(Di)]

        return (direction, shipInShore, shipInIce)
    except Exception as e:
        raise logging.warning("{} is not a valid value for code table 0739".format(Di))
        return (None, None, None)
def codeTable0877(dd):
    """
    True direction, in tens of degrees, from which wind is blowing

    :param int dd: dd
    :returns: Direction of wind in degrees
    :rtype: int
    :returns: True if wind is calm, False otherwise (dd = 00)
    :rtype: boolean
    :returns: True if wind direction is variable, from all directions or unknown, False otherwise
    :rtype: boolean
    :raises: pymetdecoder.DecodeError if dd is invalid
    """
    calm = False
    varAllUnknown = False
    direction = None
    if dd == 0:
        calm = True
    elif dd == 99:
        varAllUnknown = True
    elif 1 <= dd <= 36:
        direction = dd * 10
    else:
        raise pymetdecoder.DecodeError("{} is not a valid wind direction code for code table 0877".format(dd))

    # Return the values
    return (direction, calm, varAllUnknown)
def codeTable1600(h):
    """
    Height above surface of the base of the lowest cloud

    :param int h: h
    :returns: Lower bound of range in metres
    :rtype: int
    :returns: Upper bound of range in metres
    :rtype: int
    :returns: Quantifier (isGreaterOrEqual if h == 9)
    :rtype: string or None
    :raises: pymetdecoder.DecodeError if h is invalid
    """
    base = [0, 50, 100, 200, 300, 600, 1000, 1500, 2000, 2500, None]
    try:
        min = base[h]
        max = base[h + 1]
        if max is None:
            quantifier = "isGreaterOrEqual"
        else:
            quantifier = None
        return (min, max, quantifier)
    except KeyError as e:
        raise pymetdecoder.DecodeError("{} is not a valid code for code table 1600".format(h))
def codeTable1751(Is):
    """
    Ice accretion on ships

    :param string Is: Is
    :returns: Integer value of Is or / if unavailable
    :rtype: int or string
    :raises: pymetdecoder.DecodeError if Is is invalid
    """
    return _checkRange(Is, "1751", min=1, max=5)
def codeTable3551(Rs):
    """
    Rate of ice accretion on ships

    :param string Rs: Rs
    :returns: Integer value of Rs or / if unavailable
    :rtype: int or string
    :raises: pymetdecoder.DecodeError if Rs is invalid
    """
    return _checkRange(Rs, "3551", max=4)
def codeTable3590(RRR):
    """
    Amount of precipitation which has fallen during the reporting period

    :param int RRR: RRR
    :returns: Precipitation in mm
    :rtype: int
    :returns: Quantifier (isGreaterOrEqual if RRR == 989)
    :rtype: string or None
    :returns: True if precipitation amount measured is trace, False otherwise
    :rtype: boolean
    :raises: pymetdecoder.DecodeError if RRR is invalid
    """
    if RRR <= 988:
        return (RRR, None, False)
    elif RRR == 989:
        return (RRR, "isGreaterOrEqual", False)
    elif RRR == 990:
        return (0, None, True)
    elif 991 <= RRR <= 999:
        return ((RRR - 990) / 10.0, None, False)
    else:
        raise pymetdecoder.DecodeError("{} is not a valid precipitation code for code table 3590".format(RRR))
def codeTable3850(ss):
    """
    Indicator for sign and type of measurement of sea surface temperature

    :param string ss: ss
    :returns: Type of measurement of the sea surface temperature
    :rtype: string
    :returns: Sign of the sea surface temperature (1 if positive, -1 if negative)
    :rtype: int
    """
    if ss == "/":
        return (None, 1)
    methodList = ["Intake", "Bucket", "Hull contact sensor", "Other"]
    method = methodList[int(ss) >> 1]
    sign   = 1 if int(ss) % 2 == 0 else -1

    return (method, sign)
def codeTable3855(sw):
    """
    Indicator for sign and type of measurement of wet bulb temperature

    :param string sw: sw
    :returns: Type of measurement of the wet bulb temperature
    :rtype: string
    :returns: Sign of the wet bulb temperature (1 if positive, -1 if negative)
    :rtype: int
    """
    if sw == "/":
        return (None, 1)
    methodList = ["Measured", "Measured", "Measured", None, None, "Computed", "Computed", "Computed"]
    try:
        method = methodList[int(sw)]
        sign   = 1 if int(sw) in [0, 5] else -1
        return (method, sign)
    except KeyError as e:
        raise pymetdecoder.DecodeError("{} is not a valid code for code table 3855".format(Rs))
def codeTable4019(t):
    """
    Duration of period of reference for amount of precipitation, ending at the time of the report

    :param int t: t
    :returns: Time in hours
    :rtype: int
    :raises: pymetdecoder.DecodeError if t is invalid
    """
    hours = [None, 6, 12, 18, 24, 1, 2, 3, 9, 15]
    try:
        return hours[t]
    except KeyError as e:
        raise pymetdecoder.DecodeError("{} is not a valid code for code table 4019".format(h))
def codeTable4377(VV):
    """
    Horizontal visibility at surface

    :param int VV: VV
    :returns: Visibility in metres
    :rtype: int
    :returns: Quantifier (isLess, isGreater, isGreaterOrEqual)
    :rtype: string or None
    :raises: pymetdecoder.DecodeError if VV is invalid
    """
    visibility = None
    quantifier = None
    if 51 <= VV <= 55:
        logging.warning("{} is not a valid visibility code for code table 4377".format(VV))
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
        logging.warning("{} is not a valid visibility code for code table 4377".format(VV))

    # Return the values
    return (visibility, quantifier)
def codeTable4451(vs):
    """
    Ship's average speed made good during the three hours preceding the time of observation

    :param string vs: vs
    :returns: Minimum, maximum and quantifier of speed in knots
    :rtype: tuple (int, int, string or None)
    :returns: Minimum, maximum and quantifier of speed in km/h
    :rtype: tuple (int, int, string or None)
    """
    if vs == "/":
        return ((None, None, None), (None, None, None))
    vs = int(vs)
    if vs == 0:
        speedKT  = (0, 0, None)
        speedKMH = (0, 0, None)
    elif vs == 9:
        speedKT  = (40, None, "isGreaterThan")
        speedKMH = (75, None, "isGreaterThan")
    else:
        kmhRange = [0, 1, 11, 20, 29, 38, 48, 57, 66, 75]
        speedKT  = ((5 * vs) - 4, (5 * vs), None)
        speedKMH = (kmhRange[vs], kmhRange[vs + 1] - 1, None)

    return (speedKT, speedKMH)
