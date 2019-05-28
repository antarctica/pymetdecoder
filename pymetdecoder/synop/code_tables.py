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
import pymetdecoder, re
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
def codeTable0200(a):
    """
    Characteristic of pressure tendency during the three hours preceding the time
    of observation

    :param int a: a
    :returns: Description of code value
    :rtype: string
    :raises: pymetdecoder.DecodeError if a is invalid
    """
    descriptions = [
        "Increasing, then decreasing; atmospheric pressure the same or higher than three hours ago",
        "Increasing, then steady; or increasing, then increasing more slowly",
        "Increasing (steadily or unsteadily)",
        "Decreasing or steady, then increasing; or increasing, then increasing more rapidly",
        "Steady; atmospheric pressure the same as three hours ago",
        "Decreasing, then increasing; atmospheric pressure the same or higher than three hours ago",
        "Decreasing, then steady; or decreasing, then decreasing more slowly",
        "Decreasing (steadily or unsteadily)",
        "Steady or increasing, then decreasing; or decreasing, then decreasing more rapidly",
    ]
    try:
        return descriptions[a]
    except KeyError as e:
        raise pymetdecoder.DecodeError("{} is not a valid code for code table 0200".format(a))
def codeTable0264(a):
    """
    Standard isobaric surface for which the geopotential is reported

    :param int a3: a3
    :returns: Geopotential surface in hPa
    :rtype: int
    :raises: pymetdecoder.DecodeError if a3 is invalid
    """
    surfaces = [None, 1000, 925, None, None, 500, None, 700, 850]
    if surfaces[a] is None:
        raise pymetdecoder.DecodeError("{} is not a valid code for code table 0264".format(a))
    else:
        return surfaces[a]
def codeTable0439(bi):
    """
    Ice of land origin

    :param string bi: bi
    :returns: Description of ice of land origin
    :rtype: string
    :raises: pymetdecoder.DecodeError if bi is invalid
    """
    descriptions = [
        "No ice of land origin",
        "1-5 icebergs, no growlers or bergy bits",
        "6-10 icebergs, no growlers or bergy bits",
        "11-20 icebergs, no growlers or bergy bits",
        "Up to and including 10 growlers - no icebergs",
        "More than 10 growlers and bergy bits - no icebergs",
        "1-5 icebergs, with growlers and bergy bits",
        "6-10 icebergs, with growlers and bergy bits",
        "11-20 icebergs, with growlers and bergy bits",
        "More than 20 icebergs, with growlers and bergy bits - a major hazard to navigation"
    ]
    try:
        if bi == "/":
            return "Unable to report, because of darkness, lack of visibility or because only sea ice is visible"
        else:
            return descriptions[int(bi)]
    except KeyError as e:
        raise pymetdecoder.DecodeError("{} is not a valid code for code table 0439".format(bi))
def codeTable0639(ci):
    """
    Concentration or arrangement of sea ice

    :param string bi: ci
    :returns: Description of concentration or arrangement of sea ice
    :rtype: string
    :raises: pymetdecoder.DecodeError if ci is invalid
    """
    pass
    # descriptions = [
    #     "No sea ice in sight",
    #     "Ship in open lead more than 1.0 nautical",
    #     "6-10 icebergs, no growlers or bergy bits",
    #     "11-20 icebergs, no growlers or bergy bits",
    #     "Up to and including 10 growlers - no icebergs",
    #     "More than 10 growlers and bergy bits - no icebergs",
    #     "1-5 icebergs, with growlers and bergy bits",
    #     "6-10 icebergs, with growlers and bergy bits",
    #     "11-20 icebergs, with growlers and bergy bits",
    #     "More than 20 icebergs, with growlers and bergy bits - a major hazard to navigation"
    # ]
    # try:
    #     if bi == "/":
    #         return "Unable to report, because of darkness, lack of visibility or because only sea ice is visible"
    #     else:
    #         return descriptions[int(bi)]
    # except KeyError as e:
        # raise pymetdecoder.DecodeError("{} is not a valid code for code table 0439".format(bi))
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
    directions = ["", "NE", "E", "SE", "S", "SW", "W", "NW", "N", None]
    isCalmOrStationary = False
    allDirections = False
    if int(D) == 0:
        isCalmOrStationary = True
    elif int(D) == 9:
        allDirections = True
    direction = directions[int(D)]
    return (direction, isCalmOrStationary, allDirections)
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
    :returns: Ice accretion description
    :rtype: string
    :raises: pymetdecoder.DecodeError if Is is invalid
    """
    accretions = [
        "",
        "Icing from ocean spray",
        "Icing from fog",
        "Icing from spray and fog",
        "Icing from rain",
        "Icing from spray and rain"
    ]
    try:
        return accretions[int(Is)]
    except KeyError as e:
        raise pymetdecoder.DecodeError("{} is not a valid code for code table 1751".format(Is))
def codeTable3551(Rs):
    """
    Rate of ice accretion on ships

    :param string Rs: Rs
    :returns: Ice accretion rate
    :rtype: string
    :raises: pymetdecoder.DecodeError if Rs is invalid
    """
    rates = [
        "Ice not building up",
        "Ice building up slowly",
        "Ice building up rapidly",
        "Ice melting or breaking up slowly",
        "Ice melting or breaking up rapidly"
    ]
    try:
        return rates[int(Rs)]
    except KeyError as e:
        raise pymetdecoder.DecodeError("{} is not a valid code for code table 3551".format(Rs))
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
        raise pymetdecoder.DecodeError("{} is not a valid visibility code for code table 4377".format(VV))
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
        raise pymetdecoder.DecodeError("{} is not a valid visibility code for code table 4377".format(VV))

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
        return (None, None, None)
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
