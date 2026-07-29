"""
gpxtable - Create a markdown template from a Garmin GPX file for route information
"""

from .gpxtable import GPXTABLE_DEFAULT_WAYPOINT_CLASSIFIER, GPXTableCalculator

__version__ = "2.2.1"
__all__ = ["GPXTABLE_DEFAULT_WAYPOINT_CLASSIFIER", "GPXTableCalculator"]
__author__ = "Paul Traina"
