import gzip
import os
import sys
import unittest

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from lib.gzip_stream_reader import GzipStreamReader


class TestGzipStreamReader(unittest.TestCase):

    def test_read(self):
        with open('test/data/file.txt.gz', 'rb') as fh:
            gsr = GzipStreamReader.from_file(fh)
            result = str(gsr.read(), 'utf-8')
        with open('test/data/file.txt.gz', 'rb') as fh:
            with gzip.GzipFile(fileobj=fh, mode='r') as gh:
                expected = gh.read().decode()
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
