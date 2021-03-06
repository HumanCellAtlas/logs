import json


class JsonObjectStream:

    def __init__(self, reader):
        self.reader = reader

    def __iter__(self):
        return self

    def __next__(self):
        brackets = 0
        slash_active = False
        quotes_active = False
        result = []
        while True:
            c = self.reader.read(1)
            if c == '':
                raise StopIteration()
            result += [c]
            if c == '"':
                quotes_active = quotes_active if slash_active else (not quotes_active)
            if c == '{':
                brackets += 0 if quotes_active else 1
            if c == '}':
                brackets += 0 if quotes_active else -1
                if brackets == 0:
                    return json.loads(''.join(result))
            slash_active = (not slash_active) if c == "\\" else False
