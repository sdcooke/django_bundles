import mimetypes
import posixpath
import urllib
import os
from django.http import HttpResponse
from django.views.static import serve as django_serve

from django_bundles.core import get_bundles
from django_bundles.processors import processor_pipeline

def serve(request, path, document_root=None, show_indexes=False):
    path = posixpath.normpath(urllib.unquote(path))
    path = path.lstrip('/')
    newpath = ''
    for part in path.split('/'):
        if not part:
            # Strip empty path components.
            continue
        drive, part = os.path.splitdrive(part)
        head, part = os.path.split(part)
        if part in (os.curdir, os.pardir):
            # Strip '.' and '..' in path.
            continue
        newpath = os.path.join(newpath, part).replace('\\', '/')

    fullpath = os.path.join(document_root, newpath)

    bundles = get_bundles()

    for bundle in bundles:
        for bundle_file in bundle.files:
            if fullpath == bundle_file.file_path:
                mimetype, encoding = mimetypes.guess_type(bundle_file.file_path)
                mimetype = mimetype or 'application/octet-stream'

                f = processor_pipeline(bundle_file.processors, open(bundle_file.file_path, 'rb'))
                response = HttpResponse(f.read(), mimetype=mimetype)
                f.close()

                return response

    return django_serve(request, path, document_root=document_root, show_indexes=show_indexes)