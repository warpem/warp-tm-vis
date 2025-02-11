"""Visualize template matching results from WarpTools"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("warp-tm-vis")
except PackageNotFoundError:
    __version__ = "uninstalled"
__author__ = "Alister Burt"
__email__ = "burt.alister@gene.com"

