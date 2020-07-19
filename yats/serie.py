from yats.custom_datetime import CustomDateTime as datetime

SUPPORTED_TYPES = (str, datetime, int, bool)


class Serie(list):

    def __eq__(self, other):
        if isinstance(other, SUPPORTED_TYPES):
            return Serie([x == other for x in self])
        else:
            return super().__eq__(other)

    def __ne__(self, other):
        if isinstance(other, SUPPORTED_TYPES):
            return Serie([x != other for x in self])
        else:
            return super().__ne__(other)

    def __ge__(self, other):
        if isinstance(other, SUPPORTED_TYPES):
            return Serie([x >= other for x in self])
        else:
            return super().__ge__(other)

    def __gt__(self, other):
        if isinstance(other, SUPPORTED_TYPES):
            return Serie([x > other for x in self])
        else:
            return super().__gt__(other)

    def __le__(self, other):
        if isinstance(other, SUPPORTED_TYPES):
            return Serie([x <= other for x in self])
        else:
            return super().__le__(other)

    def __lt__(self, other):
        if isinstance(other, SUPPORTED_TYPES):
            return Serie([x < other for x in self])
        else:
            return super().__lt__(other)

    def lc(self):
        return Serie([x.lower() for x in self if x is not None])

    def uc(self):
        return Serie([x.upper() for x in self if x is not None])
