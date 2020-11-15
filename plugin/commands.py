import importlib
import os
import sublime
import sublime_plugin

from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

from lsp_utils.server_npm_resource import ServerNpmResource, get_server_npm_resource_for_package

from .patcher import AlreadyPatchedException, Patcher, restore_directory, json_dumps
from .plugin_message import console_msg, error_box, info_box
from .utils import get_command_name


def st_command_run_precheck(func: Callable):
    def wrap(self, *args, **kwargs) -> None:
        def checker() -> Tuple[ModuleType, ServerNpmResource]:
            try:
                plugin_module = importlib.import_module("LSP-intelephense.plugin")
                lsp_plugin = plugin_module.LspIntelephensePlugin  # type: ignore
            except (ImportError, AttributeError):
                raise RuntimeError("LSP-intelephense is not installed...")

            server_resource = get_server_npm_resource_for_package(
                lsp_plugin.package_name,
                lsp_plugin.server_directory,
                lsp_plugin.server_binary_path,
                lsp_plugin.package_storage(),
                lsp_plugin.minimum_node_version(),
            )  # type: Optional[ServerNpmResource]

            if not server_resource:
                raise RuntimeError("LSP-intelephense does not seem to be usable...")

            if not os.path.isfile(server_resource.binary_path):
                raise RuntimeError(
                    "The intelephense server has not been installed yet... "
                    "Open a PHP project to install it and then retry."
                )

            return (plugin_module, server_resource)

        try:
            _, server_resource = checker()
        except Exception as e:
            return error_box("[{_}] " + str(e))

        return func(self, server_resource, *args, **kwargs)

    return wrap


class PatcherLspIntelephensePatchCommand(sublime_plugin.ApplicationCommand):
    @st_command_run_precheck
    def run(self, server_resource: ServerNpmResource) -> None:
        binary_path = server_resource.binary_path

        is_already_patched = False
        is_success = False

        try:
            is_success, occurrences = Patcher.patch_file(binary_path)

            if is_success and occurrences > 0:
                info_box(
                    '[{_}] "{}" is patched with {} occurrences!\n\nRestart ST to use the premium version.',
                    binary_path,
                    occurrences,
                )
            else:
                error_box("[{_}] Unfortunately, somehow the patching failed.")
        except AlreadyPatchedException:
            is_already_patched = True
            is_success = True

        if not is_success:
            return None

        patch_info = Patcher.extract_patch_info(binary_path)

        if is_already_patched:
            msg = '[{_}] "{bin}" had been already patched...'

            if Patcher.VERSION > patch_info["version"]:
                msg += "\n\nBut the current patcher ({v_new}) is newer than the patching one ({v_old})."

            info_box(msg, bin=binary_path, v_old=patch_info["version"], v_new=Patcher.VERSION)

        console_msg("[{_}] Patch info: {}", json_dumps(patch_info))


class PatcherLspIntelephenseUnpatchCommand(sublime_plugin.ApplicationCommand):
    @st_command_run_precheck
    def run(self, server_resource: ServerNpmResource) -> None:
        binary_path = server_resource.binary_path

        restored_files = restore_directory(os.path.dirname(binary_path))

        if restored_files:
            restored_files_len = len(restored_files)

            for idx, file in enumerate(restored_files):
                console_msg("[{_}] {}/{} file restored: {}", idx + 1, restored_files_len, file)

            info_box("[{_}] {} files have been restored.", restored_files_len)
        else:
            error_box("[{_}] No file has been restored...")


class PatcherLspIntelephenseRepatchCommand(sublime_plugin.ApplicationCommand):
    @st_command_run_precheck
    def run(self, server_resource: ServerNpmResource) -> None:
        sublime.run_command(get_command_name(PatcherLspIntelephenseUnpatchCommand))
        sublime.run_command(get_command_name(PatcherLspIntelephensePatchCommand))


class PatcherLspIntelephenseOpenServerBinaryDirCommand(sublime_plugin.WindowCommand):
    @st_command_run_precheck
    def run(self, server_resource: ServerNpmResource) -> None:
        binary_path = server_resource.binary_path

        self.window.run_command("open_dir", {"dir": os.path.dirname(binary_path)})


class PatcherLspIntelephenseShowMenuCommand(sublime_plugin.WindowCommand):
    menu_items = [
        ("Patch Intelephense", PatcherLspIntelephensePatchCommand, {}),
        ("Un-patch Intelephense", PatcherLspIntelephenseUnpatchCommand, {}),
        ("Re-patch Intelephense", PatcherLspIntelephenseRepatchCommand, {}),
        ("Open Server Binary Directory", PatcherLspIntelephenseOpenServerBinaryDirCommand, {}),
    ]  # type: List[Tuple[str, type, Dict[str, Any]]]

    def run(self) -> None:
        titles, cmd_classes, cmd_args = cast(
            # make stupid type deduction tool happy
            Tuple[Tuple[str, ...], Tuple[type, ...], Tuple[Dict[str, Any], ...]],
            zip(*self.menu_items),
        )

        def on_select(idx: int) -> None:
            if idx < 0:
                return None

            self.window.run_command(get_command_name(cmd_classes[idx]), cmd_args[idx])

        self.window.show_quick_panel(titles, on_select=on_select)
