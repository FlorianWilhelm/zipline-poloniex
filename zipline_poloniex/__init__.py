# -*- coding: utf-8 -*-
import pkg_resources

try:
    __version__ = pkg_resources.get_distribution(__name__).version
except:
    __version__ = 'unknown'

# import only most import functionality for ~/.zipline/extension.py
from zipline.data.bundles import register

from .bundle import Pairs, create_bundle
