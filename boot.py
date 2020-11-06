from .plugin import set_up, tear_down
from .plugin.commands import *


def plugin_loaded() -> None:
    set_up()


def plugin_unloaded() -> None:
    tear_down()
