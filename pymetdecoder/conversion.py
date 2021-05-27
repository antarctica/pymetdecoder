################################################################################
# pymetdecoder/conversion.py
#
# Conversion functions for pymetdecoder
#
# TDBA 2020-10-20:
#   * First version
################################################################################
# CONFIGURATION
################################################################################
################################################################################
# EXCEPTION CLASSES
################################################################################
class ConversionError(Exception):
    def __init__(self, val, unit_from, unit_to):
        self.msg = "Cannot convert {} from {} to {}".format(val, unit_from, unit_to)
        super().__init__(self.msg)
################################################################################
# FUNCTIONS
################################################################################
def _convert(x, factor=1, intercept=0):
    """
    Converts a value using y = mx + c
    """
    return (factor * x) + intercept
def convert(val, unit_from, unit_to, unit_type):
    """
    Converts value from one unit to another

    :param numeric val: Value to convert
    :param str unit_from: Convert from this unit
    :param str unit_to: Convert to this unit
    :param str unit_type: Type of unit
    :returns: Converted value
    :rtype: numeric
    """
    # Run the appropriate conversion function
    if unit_type == "time":
        return _convert_time(val, unit_from, unit_to)
    elif unit_type == "length":
        # For now, only convert metric lengths (i.e. metres)
        units = []
        for u in [unit_from, unit_to]:
            if u[-1] != "m":
                raise ConversionError(val, unit_from, unit_to)
            if len(u) == 1:
                units.append(u)
            else:
                units.append(u[:-1])
        return _convert_si(val, *units)
    elif unit_type == "pressure":
        # For now, only convert metric pressures (e.g. pascals)
        units = []
        for u in [unit_from, unit_to]:
            if u[-2:] != "Pa":
                raise ConversionError(val, unit_from, unit_to)
            if len(u) == 2:
                units.append(u)
            else:
                units.append(u[:-2])
        return _convert_si(val, *units)
    elif unit_type == "speed":
        return _convert_speed(val, unit_from, unit_to)
    elif unit_type == "temperature":
        return _convert_temp(val, unit_from, unit_to)
    else:
        raise ValueError("Cannot convert unit type '{}'".format(unit_type))
def _convert_si(val, prefix_from, prefix_to):
    """
    Converts SI prefixes from one to another (e.g. from mm to km)

    :param numeric val: Value to convert
    :param str prefix_from: Prefix to convert from (e.g. "k" for "km")
    :param str prefix_to: Prefix to convert to (e.g. "k" for "km")
    :returns: Converted value
    :rtype: numeric
    """
    PREFIXES = ["m", "c", "d", None, "da", "h", "k"]
    try:
        exp_from = PREFIXES.index(prefix_from) - 3
        exp_to   = PREFIXES.index(prefix_to) - 3
        factor   = (10 ** exp_from) / (10 ** exp_to)
        return _convert(val, factor=factor)
    except Exception as e:
        raise ConversionError(val, prefix_from, prefix_to)
def _convert_time(val, unit_from, unit_to):
    """
    Converts time values from one unit to another

    :param numeric val: Value to convert
    :param str unit_from: Unit to convert from
    :param str unit_to: Unit to convert to
    :param str unit_type: Type of unit (e.g. time)
    :returns: Converted value
    :rtype: numeric
    """
    FACTORS = {
        "s": 1, "min": 60, "h": 60 * 60, "day": 60 * 60 * 24
    }
    try:
        factor = FACTORS[unit_from] / FACTORS[unit_to]
        return _convert(val, factor=factor)
    except Exception:
        raise ConversionError(val, unit_from, unit_to)
def _convert_temp(val, unit_from, unit_to):
    """
    Converts time values from one unit to another

    :param numeric val: Value to convert
    :param str unit_from: Unit to convert from
    :param str unit_to: Unit to convert to
    :returns: Converted value
    :rtype: numeric
    """
    if unit_from == unit_to:
        return val
    if unit_from == "Cel":
        if unit_to == "degF":
            # return ((9/5) * val) + 32
            return _convert(val, factor=(9/5), intercept=32)
        elif unit_to == "K":
            return _convert(val, intercept=273.15)
    elif unit_from == "degF":
        if unit_to == "Cel":
            return _convert((val - 32), factor=(5/9))
        elif unit_to == "K":
            return _convert(((val - 32) * (5/9)), intercept=273.15)
    elif unit_from == "K":
        if unit_to == "Cel":
            return _convert(val, intercept=-273.15)
        elif unit_to == "degF":
            return _convert(((9/5) * (val - 273.15)), intercept=32)

    # If we have reached this point, we are unable to convert
    raise ConversionError(val, unit_from, unit_to)
def _convert_speed(val, unit_from, unit_to):
    if unit_from == unit_to:
        return val
    if unit_from == "m/s":
        if unit_to == "KT":
            return _convert(val, factor=1.94384)
    elif unit_from == "KT":
        if unit_to == "m/s":
            return _convert(val, factor=0.51444)

    # If we have reached this point, we are unable to convert
    raise ConversionError(val, unit_from, unit_to)
