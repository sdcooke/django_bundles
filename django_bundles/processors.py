from django_bundles.conf.bundles_settings import bundles_settings
from django_bundles.utils import run_command, get_class

from StringIO import StringIO
from tempfile import NamedTemporaryFile

class Processor(object):
    """
    Definition of a file processor
    """
    requires_actual_file = False # Whether this processor needs to be passed an actual file on disk or not (StringIO might be used otherwise)

    def process_file(self, input_file):
        """
        Processes the file and returns a new file(-like) object - override this to actually do something
        """
        return input_file

class ExecutableProcessor(Processor):
    """
    A Processor that runs an external command on the file
    """
    requires_actual_file = True
    command = 'cat %(infile)s > %(outfile)s' # Define a command

    def process_file(self, input_file):
        output_file = NamedTemporaryFile()
        run_command(self.command % {'infile': input_file.name, 'outfile': output_file.name})
        return output_file

class StringProcessor(Processor):
    """
    Processor that acts using strings in some way - abstracts opening files etc
    """
    def process_string(self, input):
        """
        This should be overridden to do string processing
        """
        return input

    def process_file(self, input_file):
        output_file = StringIO()
        output_file.write(self.process_string(input_file.read()))
        return output_file

def make_actual_file(input_file):
    if not hasattr(input_file, 'name'):
        new_input_file = NamedTemporaryFile()
        new_input_file.write(input_file.read())
        input_file.close()
        input_file = new_input_file
        input_file.seek(0)
    return input_file

def processor_pipeline(processors, start_file, require_actual_file=False):
    """
    Runs a list of processors over a file and returns a file(-like) object for the processed output
    """
    input_file = start_file

    for processor in processors:
        if processor:
            input_file.seek(0)

            if processor.requires_actual_file:
                input_file = make_actual_file(input_file)

            output_file = processor.process_file(input_file)
            input_file.close()
            input_file = output_file

    if require_actual_file:
        input_file = make_actual_file(input_file)

    return input_file

class ProcessorLibrary(object):
    def get_processor(self, processor_name):
        """
        Gets an instance of a processor from a string, class or instance
        """
        if isinstance(processor_name, Processor):
            return processor_name
        if isinstance(processor_name, type) and issubclass(processor_name, Processor):
            return processor_name()
        processor_class = get_class(processor_name)
        if processor_class:
            return processor_class()
        return None

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