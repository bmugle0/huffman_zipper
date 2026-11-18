class Counter:
    def __init__(self):
        self.count = {}

    def increment(self, key, num: int=1):
        if key in self.count:
            self.count[key] += num
        else:
            self.count[key] = num

    def to_dict(self):
        return self.count

    def values(self):
        return self.to_dict().values()

    def __getitem__(self, key):
        return self.count[key]

    def __str__(self):
        return "\n".join([f"{k}: {v}" for k, v in self.count.items()])

    def ascending(self):
        return sorted(self.count.items(), key=lambda t: t[1])

    def descending(self):
        return sorted(self.count.items(), key=lambda t: t[1], reverse=True)