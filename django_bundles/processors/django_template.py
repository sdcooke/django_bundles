from django.views.debug import get_safe_settings
from django.template import engines

from django_bundles.core import get_bundles
from django_bundles.processors.base import Processor


class DjangoTemplateProcessor(Processor):
    """
    Processor that runs Django's templating code across the file - 'settings' and 'bundles' are passed into context
    Override this class to add other things to context
    """
    def get_context(self):
        """
        Override this to change context
        """
        return {
            'settings': get_safe_settings(),
            'bundles': get_bundles(),
            }

    def process(self, iter_input):
        template = engines.['django'].from_string(''.join(iter_input))
        yield template.render(self.get_context())

