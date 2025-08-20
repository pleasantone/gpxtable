"""
gpxtable - Create a markdown template from a Garmin GPX file for route information
"""

from .gpxtable import GPXTableCalculator, GPXTABLE_DEFAULT_WAYPOINT_CLASSIFIER

__version__ = "2.1.1"
__all__ = ["GPXTableCalculator", "GPXTABLE_DEFAULT_WAYPOINT_CLASSIFIER"]
__author__ = "Paul Traina"
