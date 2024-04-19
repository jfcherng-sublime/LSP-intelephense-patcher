from __future__ import annotations

import sublime


def pluginfy_msg(msg: str, *args, **kwargs) -> str:
    assert __package__
    package_name = __package__.partition(".")[0]

    return msg.format(*args, _=package_name, **kwargs)


def console_msg(msg: str, *args, **kwargs) -> None:
    print(pluginfy_msg(msg, *args, **kwargs))


def status_msg(msg: str, *args, **kwargs) -> None:
    sublime.status_message(pluginfy_msg(msg, *args, **kwargs))


def info_box(msg: str, *args, **kwargs) -> None:
    sublime.message_dialog(pluginfy_msg(msg, *args, **kwargs))


def error_box(msg: str, *args, **kwargs) -> None:
    sublime.error_message(pluginfy_msg(msg, *args, **kwargs))
