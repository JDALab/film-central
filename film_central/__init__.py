from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mov_cli.plugins import PluginHookData

from .vidsrcto import *
from .vadapav import *

plugin: PluginHookData = {
    "version": 1,
    "package_name": "film-central", # Required for the plugin update checker.
    "scrapers": {
        "DEFAULT": VidSrcToScraper,
        "vadapav": VadapavScraper,
        "vidsrcto": VidSrcToScraper
    } # NOTE: WE ARE IN NEED OF GOOD AND STABLE PROVIDERS 😭
}

__version__ = "1.3.17"