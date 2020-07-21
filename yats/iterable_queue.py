from multiprocessing import get_context
from multiprocessing.queues import Queue


class IterableQueue(Queue):

    def __init__(self, maxsize, *, ctx=None, sentinel=None):
        self.max_empty = maxsize
        self.empty_nb = 0
        super().__init__(
            maxsize=maxsize,
            ctx=ctx if ctx is not None else get_context()
        )

    def __iter__(self):
        return self

    def __next__(self):
        result = self.get()
        while result is None:
            self.empty_nb += 1
            if self.empty_nb == self.max_empty:
                raise StopIteration
            result = self.get()
        return result
