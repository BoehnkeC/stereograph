from enum import Enum, IntEnum


class TypesIndices(IntEnum):
    dummy = 0
    lines = 1
    planes = 2
    rake = 3
    circles = 4
    arcs = 5


class Types(Enum):
    dummy = "--No type--"
    lines = "Lines"
    planes = "Planes"
    rake = "Lines on Planes (Rake)"  # abweichung vom einfallen der fläche gemessen am linear
    circles = "Small Circles"
    arcs = "Arcs"


class FormatsShort:
    class Lines(Enum):
        tp = "TP"
        pq = "PQ"

    class Planes(Enum):
        ad = "AD"
        az = "AZ"


class Lines(Enum):
    dummy = "--No type--"
    pq = "Plunge, Trend Quadrant"
    ad = "Strike Azimuth, Dip Magnitude"
    az = "Unspecified, Unspecified"


class Planes(Enum):
    dummy = "--No type--"
    ad = "Strike Azimuth, Dip Magnitude"
    az = "Unspecified, Unspecified"
    qd = "Quadrant, Unspecified"
    dd = "Dip Magnitude, Dip Azimuth"


class Formats(Enum):
    tp = ("Trend", "Plunge")
    pq = ("Plunge", "Trend Quadrant")
    ad = ("Strike Azimuth", "Dip Magnitude")
    az = ("Unspecified", "Unspecified")
