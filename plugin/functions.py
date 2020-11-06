import re
import sublime


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


def get_class_command_name(cls: type) -> str:
    name = cls.__name__
    name = re.sub(r"Command$", "", name)
    name = re.sub(r"([A-Z])", r"_\1", name)
    name = re.sub(r"_{2,}", "_", name)

    return name.strip("_").lower()
