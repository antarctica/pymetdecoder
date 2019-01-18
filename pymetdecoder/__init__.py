################################################################################
# pymetdecoder/__init__.py
#
# Main __init__ script for pymetdecoder
#
# TDBA 2019-01-16:
#   * First version
################################################################################
# EXCEPTION CLASSES
################################################################################
class DecodeError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        result = self.msg
        return result
################################################################################
# BASE CLASSES
################################################################################
class Report(object):
    """
    Base class for a met report
    """
    def __init__(self, message):
        self.message = message

    def decode(self):
        """
        Decode function. Must be created in the report subclasses
        """
        raise NotImplementedError

class Observation(object):
    """
    Base class for an Observation
    """
    def __init__(self, raw, unit=None, availability=True, valueIsRaw=False, value=None):
        # Set raw attribute
        self.raw = raw

        # Set the availability
        if availability:
            self.setAvailability()

        # Set the value
        # if self.available or not availability:
        if not availability or (hasattr(self, "available") and self.available):
            if value is not None:
                setattr(self, "value", value)
            else:
                self.setValue()

        # Set the unit
        if unit is not None:
            self.setUnit(unit)

        # self.raw  = raw
        # if unit is not None:
        #     self.unit = unit
        # if availability:
        #     self.available = True

    def isAvailable(self, char="/", value=None):
        """
        Checks if the value is available
        """
        toCheck = self.raw if value is None else value
        return not bool(toCheck.count(char) == len(toCheck))
    def setAvailability(self, value=None):
        """
        Sets "available" attribute
        """
        setattr(self, "available", self.isAvailable(value=value))
    def setValue(self):
        """
        Sets "value" attribute. Unless the value is the same as the raw code
        (i.e. valueIsRaw is True), then this should be implemented in the subclass
        """
        raise NotImplementedError("setValue is not implemented for {}".format(type(self).__name__))
    def setUnit(self, unit):
        """
        Sets "unit" attribute
        """
        setattr(self, "unit", unit)

    def __repr__(self):
        return str(vars(self))
    def __str__(self):
        return self.__repr__()
################################################################################
# IMPORTS
################################################################################
from . import synop
