from django.views.debug import get_safe_settings
from django.template import Context, Template

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
        template = Template(''.join(iter_input))
        yield template.render(Context(self.get_context()))

