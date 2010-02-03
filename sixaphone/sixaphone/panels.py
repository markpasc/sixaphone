from debug_toolbar.panels import DebugPanel
from django.utils.translation import ugettext_lazy as _


class SoundManagerPanel(DebugPanel):

    name = 'SoundManager'
    has_content = True

    def title(self):
        return _("SoundManager 2")

    def nav_title(self):
        return _("SoundManager")

    def url(self):
        return ''

    def content(self):
        return '<div id="soundmanager-debug"></div>'
