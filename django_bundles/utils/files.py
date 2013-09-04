import os
import fnmatch


def expand_file_names(path, files_root):
    """
    Expands paths (e.g. css/*.css in files_root /actual/path/to/css/files/)
    """
    # For non-wildcards just return the path. This allows us to detect when
    # explicitly listed files are missing.
    if not any(wildcard in path for wildcard in '*?['):
        return [path]
    else:
        dir_path, filename = os.path.split(path)
        return [os.path.join(dir_path, f) for f in fnmatch.filter(os.listdir(os.path.join(files_root, dir_path)), filename)]


class FileChunkGenerator(object):
    def __init__(self, input_file, chunk_size=1024, close=True):
        self.input_file = input_file
        self.chunk_size = chunk_size
        self.close = close
        self.file_path = input_file.name

    def __iter__(self):
        return self

    def next(self):
        chunk = self.input_file.read(self.chunk_size)
        if chunk == '':
            if self.close:
                self.input_file.close()
            raise StopIteration
        return chunk
