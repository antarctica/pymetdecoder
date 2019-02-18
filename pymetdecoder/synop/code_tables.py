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
    Code table 0161
    A1: WMO Regional Association area in which buoy, drilling rig or oil- or gas-
        production platform has been deployed

    Returns:
        A1 (str) Region identifier (I, II etc)
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
    Code table 0200
    a: Characteristic of pressure tendency during the three hours preceding the time
       of observation

    Returns:
        a (int) Code value
        description (str) Description of code value
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
        description = descriptions[a]
        return (a, description)
    except KeyError as e:
        raise pymetdecoder.DecodeError("{} is not a valid code for code table 0200".format(a))

def codeTable0264(a):
    """
    Code table 0264
    a3: Standard isobaric surface for which the geopotential is reported

    Returns:
        surface (int) in hPa
    """
    surfaces = [None, 1000, 925, None, None, 500, None, 700, 850]
    if surfaces[a] is None:
        raise pymetdecoder.DecodeError("{} is not a valid code for code table 0264".format(dd))
    else:
        return surfaces[a]

def codeTable0877(dd):
    """
    Code table 0877
    dd: True direction, in tens of degrees, from which wind is blowing

    Returns:
        direction (int) in degrees
        calm (boolean) if wind is calm
        varAllUnknown (boolean) if wind direction is variable, from all directions or unknown
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
    Code table 1600
    h: Height above surface of the base of the lowest cloud

    Returns:
        lower bound of range (int) in metres
        upper bound of range (int) in metres
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

def codeTable3590(RRR):
    """
    Code table 3590
    RRR: Amount of precipitation which has fallen during the reporting period

    Returns:
        precipitation (int) in mm
        quantifier (str or None) (where required)
        trace (boolean)
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

def codeTable4019(t):
    """
    Code table 4019
    t: Duration of period of reference for amount of precipitation, ending at the time of the report

    Returns:
        time (int) in hours
    """
    hours = [None, 6, 12, 18, 24, 1, 2, 3, 9, 15]
    try:
        return hours[t]
    except KeyError as e:
        raise pymetdecoder.DecodeError("{} is not a valid code for code table 4019".format(h))

def codeTable4377(VV):
    """
    Code table 4377
    VV: Horizontal visibility at surface

    Returns:
        visibility (int) in metres
        quantifier (str or None) (where required)
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
