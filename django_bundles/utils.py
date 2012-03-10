import shlex
import subprocess
import os
import fnmatch

def run_command(cmd):
    """
    Runs a command - including commands with pipes - and returns (stdout, stderr)
    """
    splitcmd = cmd.split('|')
    cmds = [subprocess.Popen(shlex.split(splitcmd[0]), stdout=subprocess.PIPE, stderr=subprocess.PIPE)]
    for i, c in enumerate(splitcmd[1:]):
        cmds.append(subprocess.Popen(shlex.split(c), stdin=cmds[i - 1].stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE))
    return cmds[-1].communicate()


def get_class(class_string):
    """
    Get a class from a dotted string
    """
    split_string = class_string.encode('ascii').split('.')
    import_path = '.'.join(split_string[:-1])
    class_name = split_string[-1]

    if class_name:
        try:
            if import_path:
                mod = __import__(import_path, globals(), {}, [class_name])
                cls = getattr(mod, class_name)
            else:
                cls = __import__(class_name, globals(), {})
            if cls:
                return cls
        except (ImportError, AttributeError):
            pass

    return None

def expand_file_names(path, files_root):
    """
    Expands paths (e.g. css/*.css in files_root /actual/path/to/css/files/)
    """
    dir_path, filename = os.path.split(path)
    return [os.path.join(dir_path, f) for f in fnmatch.filter(os.listdir(os.path.join(files_root, dir_path)), filename)]
