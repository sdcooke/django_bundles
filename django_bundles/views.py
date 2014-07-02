import mimetypes
import posixpath
import urllib
import os
from operator import concat
from django.http import HttpResponse
from django.views.static import serve as django_serve

from django_bundles.core import get_bundles
from django_bundles.processors import processor_pipeline
from django_bundles.utils.files import FileChunkGenerator

from django.conf import settings


file_cache = {}


def get_file(path):
    global file_cache

    if not file_cache:
        for bundle in get_bundles():
            for bundle_file in bundle.files:
                file_cache[os.path.realpath(bundle_file.file_path)] = {
                    'bundle_file': bundle_file,
                    'cache': None
                }

    if path in file_cache:
        if not file_cache[path]['cache']:
            mimetype, encoding = mimetypes.guess_type(path)
            mimetype = mimetype or 'application/octet-stream'
            # TODO: less files need to change the way they are rendered in the template
            print "Generating", path

            file_cache[path]['cache'] = {
                'contents': reduce(concat, (chunk for chunk in processor_pipeline(file_cache[path]['bundle_file'].processors, FileChunkGenerator(open(file_cache[path]['bundle_file'].file_path, 'rb'))))),
                'mimetype': mimetype,
            }

        return file_cache[path]['cache']

    return None



def serve(request, path, document_root=None, show_indexes=False):
    if not settings.USE_BUNDLES:
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

        cached = get_file(fullpath)
        if cached:
            return HttpResponse(cached['contents'], content_type=cached['mimetype'])

    return django_serve(request, path, document_root=document_root, show_indexes=show_indexes)
