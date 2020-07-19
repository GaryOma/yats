

class RequestsHolder:

    def __init__(self):
        self.requests = []

    def __len__(self):
        return len(self.requests)

    def pop(self):
        return self.requests.pop()

    def push(self, request):
        self.requests.append(request)
