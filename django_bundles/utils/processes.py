import subprocess
import errno
import select
import os


_PIPE_BUF = getattr(select, 'PIPE_BUF', 512)


def run_process(cmd, stdin=None, iterate_stdin=True, output_chunk_size=1024, shell=True, to_close=None):
    """
    This is a modification of subprocess.Popen.communicate that accepts an iterable stdin and is itself a generator for stdout
    """
    try:
        p = subprocess.Popen(cmd, shell=shell, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if stdin:
            if iterate_stdin:
                stdin_iter = iter(stdin)
                stdin_buffer = ''
                stdin_available = True
            else:
                stdin_buffer = stdin
                stdin_available = False

        write_set = []
        read_set = []
        output_buffer = ''

        if p.stdin and stdin:
            write_set.append(p.stdin)
        if p.stdout:
            read_set.append(p.stdout)
        if p.stderr:
            read_set.append(p.stderr)

        while read_set or write_set:
            try:
                rlist, wlist, xlist = select.select(read_set, write_set, [])
            except select.error as e:
                if e.args[0] == errno.EINTR:
                    continue
                raise

            if p.stdin in wlist:
                while len(stdin_buffer) < _PIPE_BUF and stdin_available:
                    try:
                        stdin_buffer += stdin_iter.next()
                    except StopIteration:
                        stdin_available = False
                chunk = stdin_buffer[:_PIPE_BUF]
                bytes_written = os.write(p.stdin.fileno(), chunk)
                stdin_buffer = stdin_buffer[bytes_written:]

                if not (stdin_buffer or stdin_available):
                    p.stdin.close()
                    write_set.remove(p.stdin)

            if p.stdout in rlist:
                data = os.read(p.stdout.fileno(), output_chunk_size)
                if data == '':
                    p.stdout.close()
                    read_set.remove(p.stdout)
                if data:
                    output_buffer += data
                    yield data

            if p.stderr in rlist:
                data = os.read(p.stderr.fileno(), output_chunk_size)
                if data == '':
                    p.stderr.close()
                    read_set.remove(p.stderr)
                if data:
                    output_buffer += data

            if len(output_buffer) > output_chunk_size:
                output_buffer = output_buffer[-output_chunk_size:]

        return_code = p.poll()
        if return_code:
            e = subprocess.CalledProcessError(return_code, cmd)
            e.output = output_buffer
            raise e
    finally:
        if to_close:
            to_close.close()
