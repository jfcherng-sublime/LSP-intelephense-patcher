import importlib
import os
import sublime
import sublime_plugin

from types import ModuleType
from typing import Optional

from .functions import console_msg, error_box, info_box, get_class_command_name
from .patcher import AlreadyPatchedException, Patcher


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


class PatchLspIntelephenseCommand(sublime_plugin.ApplicationCommand):
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
                    "Restart ST to make it premium.".format(binary_path, occurrences)
                )
            else:
                is_success = False
                error_box("Unfortunately, somehow the patching failed.")
        except AlreadyPatchedException:
            is_success = True
            info_box('"{}" had been already patched...'.format(binary_path))

        if is_success:
            console_msg("Patch info: {}".format(Patcher.json_dumps_better(Patcher.extract_patch_info(binary_path))))


class UnpatchLspIntelephenseCommand(sublime_plugin.ApplicationCommand):
    def run(self) -> None:
        plugin_module = st_command_precheck()

        if not plugin_module:
            return None

        lsp_plugin = plugin_module.LspIntelephensePlugin  # type: ignore
        binary_path = lsp_plugin.binary_path()  # type: str

        restored_files = Patcher.restore_directory(os.path.dirname(binary_path))

        if restored_files:
            for idx, file in enumerate(restored_files):
                console_msg("{}/{} file restored: {}".format(idx + 1, len(restored_files), file))

            info_box("{} files have been restored.".format(len(restored_files)))
        else:
            error_box("No file has been restored...")


class RepatchLspIntelephenseCommand(sublime_plugin.ApplicationCommand):
    def run(self) -> None:
        plugin_module = st_command_precheck()

        if not plugin_module:
            return None

        sublime.run_command(get_class_command_name(UnpatchLspIntelephenseCommand))
        sublime.run_command(get_class_command_name(PatchLspIntelephenseCommand))


class LspIntelephenseOpenServerBinaryDirCommand(sublime_plugin.WindowCommand):
    def run(self) -> None:
        plugin_module = st_command_precheck()

        if not plugin_module:
            return None

        lsp_plugin = plugin_module.LspIntelephensePlugin  # type: ignore
        binary_path = lsp_plugin.binary_path()  # type: str

        self.window.run_command("open_dir", {"dir": os.path.dirname(binary_path)})
