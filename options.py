from enum import Enum, IntEnum


class TypesIndices(IntEnum):
    dummy = 0
    lines = 1
    planes = 2
    rake = 3
    circles = 4
    arcs = 5


class Types(Enum):
    dummy = ""
    lines = "Lines"
    planes = "Planes"
    rake = "Lines on Planes (Rake)"  # abweichung vom einfallen der fläche gemessen am linear
    circles = "Small Circles"
    arcs = "Arcs"


class Formats:
    class Lines(Enum):
        tp = "TP"
        pq = "PQ"

    class Planes(Enum):
        ad = "AD"
        az = "AZ"
