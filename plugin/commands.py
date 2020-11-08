import importlib
import os
import sublime
import sublime_plugin

from types import ModuleType
from typing import Any, Dict, List, Optional, Tuple, cast

from .functions import console_msg, error_box, info_box, get_class_command_name
from .patcher import AlreadyPatchedException, Patcher, restore_directory, json_dumps_better


def st_command_precheck() -> Optional[ModuleType]:
    try:
        plugin_module = importlib.import_module("LSP-intelephense.plugin")
    except ImportError:
        error_box('"LSP-intelephense" is not installed.')
        return None

    lsp_plugin = plugin_module.LspIntelephensePlugin  # type: ignore
    binary_path = lsp_plugin.binary_path()  # type: str

    if not binary_path:
        error_box('"LSP-intelephense" seems not initiated. Please open a PHP project and retry.')
        return None

    return plugin_module


class PatcherLspIntelephensePatchCommand(sublime_plugin.ApplicationCommand):
    def run(self) -> None:
        plugin_module = st_command_precheck()

        if not plugin_module:
            return None

        lsp_plugin = plugin_module.LspIntelephensePlugin  # type: ignore
        binary_path = lsp_plugin.binary_path()  # type: str

        try:
            is_success, occurrences = Patcher.patch_file(binary_path)

            if is_success and occurrences > 0:
                info_box(
                    '"{}" is patched with {} occurrences!\n\n'
                    "Restart ST to use the premium version.".format(binary_path, occurrences)
                )
            else:
                is_success = False
                error_box("Unfortunately, somehow the patching failed.")
        except AlreadyPatchedException:
            is_success = True
            info_box('"{}" had been already patched...'.format(binary_path))

        if is_success:
            console_msg("Patch info: {}".format(json_dumps_better(Patcher.extract_patch_info(binary_path))))


class PatcherLspIntelephenseUnpatchCommand(sublime_plugin.ApplicationCommand):
    def run(self) -> None:
        plugin_module = st_command_precheck()

        if not plugin_module:
            return None

        lsp_plugin = plugin_module.LspIntelephensePlugin  # type: ignore
        binary_path = lsp_plugin.binary_path()  # type: str

        restored_files = restore_directory(os.path.dirname(binary_path))

        if restored_files:
            restored_files_len = len(restored_files)

            for idx, file in enumerate(restored_files):
                console_msg("{}/{} file restored: {}".format(idx + 1, restored_files_len, file))

            info_box("{} files have been restored.".format(restored_files_len))
        else:
            error_box("No file has been restored...")


class PatcherLspIntelephenseRepatchCommand(sublime_plugin.ApplicationCommand):
    def run(self) -> None:
        plugin_module = st_command_precheck()

        if not plugin_module:
            return None

        sublime.run_command(get_class_command_name(PatcherLspIntelephenseUnpatchCommand))
        sublime.run_command(get_class_command_name(PatcherLspIntelephensePatchCommand))


class PatcherLspIntelephenseOpenServerBinaryDirCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        plugin_module = st_command_precheck()

        if not plugin_module:
            return None

        lsp_plugin = plugin_module.LspIntelephensePlugin  # type: ignore
        binary_path = lsp_plugin.binary_path()  # type: str

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

            self.window.run_command(get_class_command_name(cmd_classes[idx]), cmd_args[idx])

        self.window.show_quick_panel(titles, on_select=on_select)
