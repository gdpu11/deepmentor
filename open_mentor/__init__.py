"""Compatibility module for the legacy open_mentor package; use deepmentor instead."""
from __future__ import annotations

import warnings

from deepmentor import __version__
from deepmentor.library import Library

warnings.warn("The 'open_mentor' package is deprecated. Please migrate to 'deepmentor'.", DeprecationWarning, stacklevel=2)

__all__ = ["__version__", "Library"]
