import io
import zlib
from enum import Enum
from itertools import chain


class GzipStreamReader(io.RawIOBase):

    class States(Enum):
        START = 1
        STOP = 2

    def __init__(self, generator):
        self.generator = generator
        super().__init__()

    def readable(self,):
        return True

    @classmethod
    def from_file(cls, file_obj):
        return cls(GzipStreamReader._decompress_as_stream(file_obj))

    def read(self, size=-1) -> bytes:
        remaining = size
        result = bytearray()
        while True:
            if remaining == 0:
                break
            tmp = self._pop()
            if tmp == self.States.STOP:
                break
            result.append(tmp)
            if remaining > 0:
                remaining -= 1
        return result

    def _pop(self):
        tmp = next(self.generator, self.States.STOP)
        return tmp

    def readall(self):
        return self.read()

    def write(self, b):
        self.generator = chain(self.generator, self._to_generator(b))

    @staticmethod
    def _to_generator(b):
        for c in b:
            yield c

    @staticmethod
    def _decompress_as_stream(file_obj):
        decompressor = zlib.decompressobj(16+zlib.MAX_WBITS)
        while True:
            # https://stackoverflow.com/questions/37176508/how-does-deflatezlib-determine-block-size
            data_to_decompress = file_obj.read(16384)
            if not data_to_decompress:
                break
            decompressed = decompressor.decompress(data_to_decompress)
            for byte in bytearray(decompressed):
                yield byte
