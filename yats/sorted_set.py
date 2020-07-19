import sys
import bisect
import json
import csv
import re

from src.serie import Serie
from src.sorted_element import SortedElement
from src.custom_datetime import CustomDateTime as datetime


class SortedSet:

    def __init__(self, init):
        self.list = list(init)

    def __len__(self):
        return len(self.list)

    def __iter__(self):
        return self.list.__iter__()

    def __next__(self):
        return self.list.__next__()

    def _get_list_attribute(self, att):
        return [getattr(x, att) for x in super().__getattribute__("list")]

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.list[item]
        elif isinstance(item, slice):
            return type(self)(self.list[item])
        elif isinstance(item, tuple):
            cols = []
            for it in item:
                cols.append(self._get_list_attribute(it))
            return Serie(zip(*cols))
        elif isinstance(item, Serie):
            init_list = [x[0] for x in zip(self.list, item) if x[1]]
            return type(self)(init_list)
        else:
            return Serie(self._get_list_attribute(item))

    def __getattribute__(self, name):
        try:
            attr = super().__getattribute__(name)
        except AttributeError:
            attr = Serie(self._get_list_attribute(name))
        return attr

    def add(self, data):
        if isinstance(data, SortedSet):
            beg = 0
            for element in data:
                idx = bisect.bisect(self.list, element, lo=beg)
                if 0 < idx < len(self.list) and element == self.list[idx]:
                    print("DUPLICATE", element)
                    print(element.id)
                    print(self.id)
                    sys.exit(0)
                else:
                    self.list.insert(idx, element)
                beg = idx
        else:
            idx = bisect.bisect(self.list, data)
            # bisect.insort(self.list, data)
            # return
            if 0 < idx < len(self.list) and data == self.list[idx]:
                pass
            else:
                self.list.insert(idx, data)

    def export(self, output):
        extension = re.search(r".+\.(\S+)$", output).group(1)
        if extension == "json":
            with open(output, 'w') as outfile:
                json.dump(self.list, outfile, cls=SortedListEncoder, indent=4)
        elif extension == "csv":
            with open(output, 'w', newline='') as csvfile:
                fieldnames = self.list[0].to_dict().keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames,
                                        quoting=csv.QUOTE_NONNUMERIC)

                writer.writeheader()
                for element in self.list:
                    writer.writerow(element.to_dict())


class SortedListEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, SortedElement):
            return o.to_dict()
        if isinstance(o, datetime):
            return o.isoformat()
        else:
            return json.JSONEncoder.default(self, o)
