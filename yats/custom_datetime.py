from datetime import datetime


class CustomDateTime(datetime):

    def __repr__(self):
        return self.strftime("<%Y-%m-%d %H:%M:%S>")
