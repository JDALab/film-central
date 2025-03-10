from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mov_cli.plugins import PluginHookData

from .catflix import *
from .bflix import *
from .vadapav import *
from .vidsrcto import *

plugin: PluginHookData = {
    "version": 1,
    "package_name": "film-central", # Required for the plugin update checker.
    "scrapers": {
        "DEFAULT": CatFlix,
        "ANDROID.DEFAULT": VadapavScraper,
        "IOS.DEFAULT": VadapavScraper,
        "catflix": CatFlix, # Experimental
        "bflix": BFlix, # Experimental
        "vadapav": VadapavScraper,
        "vidsrcto": VidSrcToScraper,
    }
}

__version__ = "1.5"