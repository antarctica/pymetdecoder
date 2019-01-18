################################################################################
# pymetdecoder/__init__.py
#
# Main __init__ script for pymetdecoder
#
# TDBA 2019-01-16:
#   * First version
################################################################################
# CONFIGURATION
################################################################################
from . import synop
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
# REPORT CLASSES
################################################################################
class Report(object):
    """Base class for a met report"""
    def __init__(self, message):
        self.message = message

    def decode(self):
        """Decode function. Must be created in the report subclasses"""
        raise NotImplementedError
