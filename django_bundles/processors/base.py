from django_bundles.conf.bundles_settings import bundles_settings
from django_bundles.utils import get_class
from django_bundles.utils.files import FileChunkGenerator
from django_bundles.utils.processes import run_process
from django.core.exceptions import ImproperlyConfigured

from tempfile import NamedTemporaryFile
import collections


class Processor(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def process(self, iter_input):
        raise NotImplementedError


class ExecutableProcessor(Processor):
    command = None

    def process(self, iter_input):
        input_file = output_file = None
        stdin = iter_input
        format_kwargs = {}

        # Create temporary files for input and output if required
        if '{infile}' in self.command:
            stdin = None

            if hasattr(iter_input, 'file_path'):
                format_kwargs['infile'] = iter_input.file_path
            else:
                input_file = NamedTemporaryFile()
                format_kwargs['infile'] = input_file.name

                for chunk in iter_input:
                    input_file.write(chunk)

                input_file.seek(0) # Not sure why this is needed

        if '{outfile}' in self.command:
            output_file = NamedTemporaryFile()
            format_kwargs['outfile'] = output_file.name

        command = self.command.format(**format_kwargs)

        g = run_process(command, stdin=stdin, to_close=input_file)

        if output_file:
            # Consume the iterator into a zero length deque
            collections.deque(g, maxlen=0)
            return FileChunkGenerator(output_file)
        else:
            return g


def processor_pipeline(processors, iter_input):
    pipeline = iter_input

    for processor in processors:
        if not processor:
            continue

        pipeline = processor.process(pipeline)

    return pipeline


class ProcessorLibrary(object):
    def get_processor(self, processor_defn):
        class_path, init_kwargs = None, {}
        if isinstance(processor_defn, basestring):
            class_path = processor_defn
        elif isinstance(processor_defn, (list, tuple)):
            if len(processor_defn) == 1:
                class_path = processor_defn[0]
            elif len(processor_defn) == 2:
                class_path, init_kwargs = processor_defn

        if class_path:
            processor_class = get_class(class_path)

            if processor_class:
                return processor_class(**init_kwargs)

        raise ImproperlyConfigured("Invalid processor: %s" % repr(processor_defn))

    def get_processors(self, processors):
        return [instance for instance in (self.get_processor(processor) for processor in processors) if instance]

    def get_default_preprocessors_for(self, file_type):
        if file_type in bundles_settings.DEFAULT_PREPROCESSORS:
            return self.get_processors(bundles_settings.DEFAULT_PREPROCESSORS[file_type])
        return []

    def get_default_postprocessors_for(self, bundle_type):
        if bundle_type in bundles_settings.DEFAULT_POSTPROCESSORS:
            return self.get_processors(bundles_settings.DEFAULT_POSTPROCESSORS[bundle_type])
        return []

processor_library = ProcessorLibrary()