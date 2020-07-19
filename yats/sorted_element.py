

class SortedElement:

    def __init__(self, sorted_keys):
        self.SORT_KEYS = sorted_keys

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        for key in self.SORT_KEYS:
            if getattr(self, key) < getattr(other, key):
                return True
        return False

    def to_dict(self):
        return self.__dict__
