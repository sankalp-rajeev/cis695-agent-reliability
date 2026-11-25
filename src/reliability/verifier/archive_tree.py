"""Base-archive repository view used by the frozen V2 selection method."""

import tarfile


class ArchiveTree:
    def __init__(self, path):
        self.archive = tarfile.open(path)
        self.files = tuple(sorted(m.name.removeprefix('testbed/')
                                  for m in self.archive.getmembers()
                                  if m.name.startswith('testbed/') and not m.isdir()))
        self.cache = {}

    def list_files(self):
        return self.files

    def read_text(self, path):
        if path not in self.cache:
            self.cache[path] = self.archive.extractfile('testbed/' + path).read().decode('utf-8', errors='replace')
        return self.cache[path]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.archive.close()
