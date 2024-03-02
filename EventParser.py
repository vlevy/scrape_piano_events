import re
from datetime import timedelta

from parser_common_code import any_match


class EventParser(object):
    """Base class for event parsing"""
