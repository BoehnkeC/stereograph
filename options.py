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


class FormatsIndices(IntEnum):
    def __init__(self, _type_index=TypesIndices.dummy):
        super().__init__()
        if _type_index == TypesIndices.lines:
            tp = 0
            pq = 1
            ll = 2
            rk = 3


class Formats:
    class Lines(Enum):
        tp = "TP"
        pq = "PQ"

    class Planes(Enum):
        ad = "AD"
        az = "AZ"


# class Formats(Enum):
#     def __init__(self, _type_index=TypesIndices.dummy):
#         super().__init__()
#         if _type_index == TypesIndices.lines:
#             tp = "TP"
#             pq = "PQ"
#             ll = "LL"
#             rk = "RK"


#class Formats(Enum, TypesIndices):
#    if TypesIndices.lines:
#        tp = ("Trend", "Plunge")
