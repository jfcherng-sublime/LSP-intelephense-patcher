def plugin_reload() -> None:
    import sys

    prefix = __package__ + "."
    for module_name in tuple(filter(lambda m: m.startswith(prefix) and m != __name__, sys.modules)):
        del sys.modules[module_name]


plugin_reload()

from .plugin import set_up
from .plugin import tear_down
from .plugin.commands import *


def plugin_loaded() -> None:
    set_up()


def plugin_unloaded() -> None:
    tear_down()
