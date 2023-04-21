################################################################################
# pymetdecoder/__init__.py
#
# Main __init__ script for pymetdecoder
#
# TDBA 2019-01-16:
#   * First version
# TDBA 2023-04-14:
#   * Removed logging configuration (#8)
# TDBA 2023-04-21:
#   * Rainfall group in section 3 now decodes properly if cloud group (or other
#     group) follows (#9)
################################################################################
# IMPORTS
################################################################################
import sys, json, logging, re
from . import conversion
################################################################################
# EXCEPTION CLASSES
################################################################################
class DecodeError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        result = self.msg
        return result
class EncodeError(Exception):
    def __init__(self, msg):
        self.msg = "encoding error: {}".format(msg)
        super().__init__(self.msg)
class InvalidCode(Exception):
    def __init__(self, val, desc):
        self.msg = "{} is not a valid code for {}".format(val, desc)
        super().__init__(self.msg)
class InvalidGroup(Exception):
    def __init__(self, group):
        self.msg = "{} is not a valid group".format(group)
        super().__init__(self.msg)
################################################################################
# BASE CLASSES
################################################################################
class Report(object):
    """
    Base class for a meteorological report

    :param message string: Message to parse
    """
    def __init__(self):
        self.not_implemented = []
    def decode(self, message):
        """
        Decode function
        """
        try:
            return self._decode(message)
        except Exception as e:
            raise DecodeError(str(e))
        # raise NotImplementedError("decode is not implemented for {}".format(type(self).__name__))
    def encode(self, data):
        """
        Encode function
        """
        try:
            return self._encode(data)
        except Exception as e:
            raise EncodeError(str(e))
        # raise NotImplementedError("encode is not implemented for {}".format(type(self).__name__))
    def _decode(self, message):
        """
        Actual decode function. Implement in subclass
        """
        raise NotImplementedError("_decode needs to be implemented in {} subclass".format(type(self).__name__))
    def _encode(self, data):
        """
        Actual encode function. Implement in subclass
        """
        raise NotImplementedError("_encode needs to be implemented in {} subclass".format(type(self).__name__))
    def toJSON(self):
        return json.dumps(self.data, cls=ObsEncoder)
class Observation(object):
    """
    Base class for an Observation

    :param string/int raw: Raw value of observation
    :param string unit: Unit of measurement for the observation
    :param boolean availability: Check for the availability of this observation
    :param anything value: Calculated value of the observation
    :param boolean noValAttr: If true, do not set value attribute for this observation
    """
    # def __init__(self, raw, unit=None, availability=True, value=None, noValAttr=False):
    def __init__(self, null_char="/"):
        self.null_char = null_char
        if hasattr(self, "_CODE_LEN") and not hasattr(self, "_ENCODE_DEFAULT"):
            self._ENCODE_DEFAULT = null_char * self._CODE_LEN
        self._init_obs()
    def _init_obs(self):
        pass
    def decode(self, raw, **kwargs):
        """
        Decodes raw value into observation value(s)
        """
        try:
            # Check if available
            if not self.is_available(raw):
                return None

            # Check if valid
            if not self.is_valid(raw, **kwargs):
                return None

            # Decode
            return self._decode(raw, **kwargs)
        except NotImplementedError as e:
            logging.error(str(e))
            sys.exit(1)
        except InvalidCode as e:
            # logging.warning(str(e))
            raise DecodeError(str(e))
        except Exception as e:
            # logging.warning(str(e))
            raise DecodeError("Unable to decode group {}".format(raw))
    def encode(self, raw, **kwargs):
        """
        Encodes observation into a coded value
        """
        try:
            # Get the group, if present
            group = kwargs.get("group", None)

            # If value is None, return default. Otherwise, return encoded value
            allow_none = kwargs.get("allow_none", False)
            if not allow_none and not hasattr(self, "_CODE_TABLE"):
                if raw is None:
                    val = self._ENCODE_DEFAULT
                elif isinstance(raw, dict) and "value" in raw and raw["value"] is None:
                    val = self._ENCODE_DEFAULT
                else:
                    val = self._encode(raw, **kwargs)
            else:
                val = self._encode(raw, **kwargs)

            # Return output
            if group is None:
                return val
            else:
                return "{}{}".format(group, val)
        except NotImplementedError as e:
            logging.error(str(e))
            sys.exit(1)
        except conversion.ConversionError as e:
            logging.warning(str(e))
        except Exception as e:
            logging.warning("No valid {}. Using {}".format(type(self).__name__, self._ENCODE_DEFAULT))
            if "group" in kwargs:
                return "{}{}".format(kwargs.get("group"), self._ENCODE_DEFAULT)
            else:
                return self._ENCODE_DEFAULT
    def _decode(self, raw, **kwargs):
        """
        Actual decode function. Mostly implemented in subclasses
        """
        if not hasattr(self, "_COMPONENTS"):
            return self._decode_value(raw, **kwargs)
        else:
            retval = {}
            for x in self._COMPONENTS:
                retval[x[0]] = x[3]().decode(raw[x[1]:x[1] + x[2]])
            return retval
        # raise NotImplementedError("_decode needs to be implemented in {} subclass".format(type(self).__name__))
    def _encode(self, data, **kwargs):
        """
        Actual encode function. Mostly implemented in subclasses
        """
        if not hasattr(self, "_COMPONENTS"):
            return self._encode_value(data, **kwargs)
        else:
            retval = []
            for x in self._COMPONENTS:
                retval.append(x[3]().encode(data[x[0]] if x[0] in data else None))
            return "".join(retval)
        # raise NotImplementedError("_encode needs to be implemented in {} subclass".format(type(self).__name__))
    def is_available(self, value, char="/"):
        """
        Checks if the value is available

        :param anything value: Value to check
        :param string char: Character to use to determine if value is available
        :returns: False if value is not available (i.e. report contains /), otherwise True
        :rtype: boolean
        """
        if value is None:
            return False
        return not bool(value.count(char) == len(value))
        # toCheck = str(self.raw) if value is None else str(value)
        # return not bool(toCheck.count(char) == len(toCheck))
    def is_valid(self, value=None, raise_exception=True, name=None, **kwargs):
        """
        Checks if the value is valid. Wrapper to _is_valid()

        :param anything value: Value to check
        :param boolean raise_exception: If True, raises exception if not valid
        :returns: True if value is valid, False otherwise
        :rtype: boolean
        """
        valid = self._is_valid(value, **kwargs)
        if not valid:
            foo = InvalidCode(value, type(self).__name__)
            if raise_exception:
                raise foo
            else:
                logging.warning(foo.msg)
        return valid
    def _is_valid(self, value, **kwargs):
        """
        Actual validity check

        :returns: True if value is valid, False otherwise
        :rtype: boolean
        """
        try:
            # Check if value is available. If not, it passes validity
            if not self.is_available(value=value):
                return True

            # If _VALID_VALUES present, use that to check
            if hasattr(self, "_VALID_VALUES"):
                if value in self._VALID_VALUES:
                    return True
                else:
                    return False

            # If _VALID_RANGE present, check if value is in range
            if hasattr(self, "_VALID_RANGE"):
                value = float(value)
                if self._VALID_RANGE[0] <= value <= self._VALID_RANGE[1]:
                    return True
                else:
                    return False

            # If _VALID_REGEXP present, check value matches regexp
            if hasattr(self, "_VALID_REGEXP"):
                if re.match(self._VALID_REGEXP, value):
                    return True
                else:
                    return False

            # If we have reached this point, we can't validate. Therefore, assume it's valid
            return True
        except:
            # In the event of an exception (usually caused by non valid characters),
            # assume value is invalid
            return False
    def _decode_value(self, val, **kwargs):
        try:
            # Get unit
            unit = kwargs.get("unit")
            if unit is None and hasattr(self, "_UNIT"):
                unit = self._UNIT

            # Get value from code table
            if hasattr(self, "_CODE_TABLE"):
                table_opts = {}
                if hasattr(self, "_TABLE"):
                    table_opts["table"] = self._TABLE
                out_val = self._CODE_TABLE(**table_opts).decode(val, **kwargs)
                if self._CODE_TABLE.__name__ != "CodeTableSimple" and out_val is not None:
                    if isinstance(out_val, list):
                        for a in out_val:
                            a["_code"] = int(val)
                    else:
                        out_val["_code"] = int(val)
            else:
                out_val = val

            # Return None if out_val is none
            if out_val is None:
                return None

            # Convert to int
            out_val = int(out_val) if not isinstance(out_val, (dict, list)) else out_val

            # Perform post conversion
            out_val = self._decode_convert(out_val, **kwargs)

            # Create and return output
            data = { "value": out_val } if not isinstance(out_val, (dict, list)) else out_val
            if unit is not None:
                data["unit"] = unit
            return data
        except ValueError as e:
            logging.warning(InvalidCode(val, type(self).__name__))
            return None
        except Exception as e:
            logging.warning(str(e))
            return None
    def _encode_value(self, data, **kwargs):
        try:
            # Get value from code table. If no code table, use value attribute
            if hasattr(self, "_CODE_TABLE"):
                table_opts = {}
                if hasattr(self, "_TABLE"):
                    table_opts["table"] = self._TABLE
                out_val = self._CODE_TABLE(**table_opts).encode(data)
            else:
                out_val = data["value"] if "value" in data else None

            # Convert value
            out_val = self._encode_convert(out_val, **kwargs)

            # Return code
            return ("{:0" + str(self._CODE_LEN) + "d}").format(int(out_val))
        except Exception as e:
            # print(str(e))
            return self._ENCODE_DEFAULT

    def _decode_convert(self, val, **kwargs):
        return val
    def _encode_convert(self, val, **kwargs):
        return val

    def __repr__(self):
        return str(vars(self))
    def __str__(self):
        return self.__repr__()
class ObsEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__
################################################################################
# FUNCTIONS
################################################################################
def decode_attribute(val, unit=None, post_func=None):
    try:
        # Convert to int
        out_val = int(val)

        # Perform post conversion
        if post_func is not None:
            out_val = post_func(out_val)

        data = { "value": out_val }
        if unit is not None:
            data["unit"] = unit
        return data
    except Exception:
        return None
def encode_attribute(data, attr, len, def_unit=None, unit_type=None, null_char="/", code_table=None, post_func=None, val_range=None):
    # Set null output
    null_output = null_char * len

    try:
        if attr is None:
            d = data
        elif attr in data and data[attr] is not None:
            d = data[attr]
        else:
            return null_output

        # If using a code table, obtain code from there
        # Otherwise, calculate code
        if code_table is not None:
            out_val = code_table().encode(d)
        else:
            # If data is a dict, get the value and unit from the attributes
            # Otherwise, assume value is raw data in the default units
            if isinstance(d, dict):
                val  = d["value"]
                unit = d["unit"] if "unit" in d else def_unit
            else:
                val  = d
                unit = def_unit

            # Convert if required
            if def_unit is not None:
                out_val = conversion.convert(val, unit, def_unit, unit_type)
            else:
                out_val = val

            # Check value is within range
            if val_range is not None:
                if not val_range[0] <= out_val <= val_range[1]:
                    raise Exception

        # Perform post conversion
        if post_func is not None:
            out_val = post_func(out_val)

        # Return code
        return ("{:0" + str(len) + "d}").format(int(out_val))
    except Exception as e:
        return null_output
