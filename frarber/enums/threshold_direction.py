from enum import Enum


class ThresholdDirection(str, Enum):
    """Direction for threshold crossing alerts."""

    ABOVE = "above"
    BELOW = "below"
