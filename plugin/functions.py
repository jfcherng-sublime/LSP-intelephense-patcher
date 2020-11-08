import re
import sublime

from typing import Union


def pluginfy_msg(msg: str) -> str:
    PACKAGE_NAME = __package__.partition(".")[0]

    return "[{}] {}".format(PACKAGE_NAME, msg)


def console_msg(msg: str) -> None:
    print(pluginfy_msg(msg))


def status_msg(msg: str) -> None:
    sublime.status_message(pluginfy_msg(msg))


def info_box(msg: str) -> None:
    sublime.message_dialog(pluginfy_msg(msg))


def error_box(msg: str) -> None:
    sublime.error_message(pluginfy_msg(msg))


def get_command_name(var: Union[type, str]) -> str:
    name = var.__name__ if isinstance(var, type) else str(var)

    name = re.sub(r"Command$", "", name)
    name = re.sub(r"([A-Z])", r"_\1", name)
    name = re.sub(r"_{2,}", "_", name)

    return name.strip("_").lower()
