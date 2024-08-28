from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mov_cli.plugins import PluginHookData

from .bflix import *
from .vadapav import *
from .vidsrcto import *

plugin: PluginHookData = {
    "version": 1,
    "package_name": "film-central", # Required for the plugin update checker.
    "scrapers": {
        "DEFAULT": BFlix,
        "ANDROID.DEFAULT": VadapavScraper,
        "IOS.DEFAULT": VadapavScraper,
        "bflix": BFlix, # Experimental
        "vadapav": VadapavScraper,
        "vidsrcto": VidSrcToScraper,
    }
}

__version__ = "1.4"