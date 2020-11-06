import datetime
import io
import json
import os
import re
import shutil

from typing import Any, Dict, Iterable, List, Optional, Tuple


class AlreadyPatchedException(Exception):
    def __init__(self, message: str = "") -> None:
        super().__init__(message or '"intelephense" had been patched...')


class Patcher:
    VERSION = "1.1.0"

    PATCH_INFO_MARKERS = ("--- PATCH_INFO_BEGIN ---", "--- PATCH_INFO_END ---")
    PATCHED_MARKER_DETECTION = "/** FILE HAS BEEN PATCHED **/"

    # fmt: off
    PATCHED_MARKER = "\n".join([
        PATCHED_MARKER_DETECTION,
        "/** " + PATCH_INFO_MARKERS[0] + " {info} " + PATCH_INFO_MARKERS[1] + " **/",
    ])
    # fmt: on

    LICENSE_OBJECT = {
        "message": {
            "timestamp": 0,
            "machineId": "YOUR_MACHINE_ID",
            "licenceKey": "YOUR_LICENCE_KEY",
            "expiryTimestamp": 99999999999,
            "resultCode": 1,  # 0: invalid, 1: valid, 3: revoked
        },
        "signature": "THE_CALCULATED_SIGNATURE",
    }

    @classmethod
    def patch_file(cls, path: str) -> Tuple[bool, int]:
        if not path or not os.path.isfile(path):
            return (False, 0)

        cls.backup_files([path])

        content = cls.file_get_content(path) or ""
        content, occurrences = cls.patch_str(content)

        if occurrences == 0:
            return (False, 0)

        is_success = cls.file_set_content(path, content)

        return (is_success, occurrences)

    @classmethod
    def patch_str(cls, content: str) -> Tuple[str, int]:
        if content.rfind(cls.PATCHED_MARKER_DETECTION) > -1:
            raise AlreadyPatchedException()

        occurrences = 0
        for search, replace, flags, count in cls.get_patch_patterns():
            content, occurrence = re.subn(search, replace, content, max(0, count), flags)
            occurrences += occurrence

        return (
            content.rstrip() + "\n\n" + cls.generate_patch_marker(occurrences) + "\n",
            occurrences,
        )

    @classmethod
    def get_patch_patterns(cls) -> List[Tuple[str, str, int, int]]:
        LICENSE_OBJECT_JS = cls.json_dumps_better(cls.LICENSE_OBJECT)

        return [
            # force convert licenceKey into a non-empty string even if it is undefined
            (r"(\.initializationOptions\.licenceKey)(?![;)\]}])", r"\1 + 'FOO_BAR'", re.UNICODE, 0),
            (r"(\.initializationOptions\.licenceKey)(?=[;)\]}])", r"\1 = 'FOO_BAR'", re.UNICODE, 0),
            # license always active
            (
                # patch the setter of "activationResult"
                r"\b(activationResult\([^)]*\)\s*\{)",
                r"\1return this._activationResult = " + LICENSE_OBJECT_JS + ";",
                re.UNICODE,
                0,
            ),
            (
                # this one is just used to trigger the setter of "activationResult"
                r"\b(readActivationResultFromCache\([^)]*\)\s*\{)",
                r"\1return this.activationResult = {};",
                re.UNICODE,
                0,
            ),
            # nullify potential telemetry
            (r"\b(intelephense\.com)", r"localhost", re.UNICODE, 0),
        ]

    @classmethod
    def generate_patch_marker(cls, occurrences: int = 0) -> str:
        return cls.PATCHED_MARKER.format(
            info=json.dumps(
                {
                    "patcher": __file__,
                    "version": cls.VERSION,
                    "occurrences": occurrences,
                    "time": datetime.datetime.now().replace(microsecond=0).isoformat(),
                }
            )
        )

    @classmethod
    def extract_patch_info(cls, path_or_content: str) -> Dict[str, Any]:
        content = cls.file_get_content(path_or_content) or path_or_content

        idx_begin = content.rfind(cls.PATCH_INFO_MARKERS[0])
        if idx_begin < 0:
            return {}

        idx_end = content.rfind(cls.PATCH_INFO_MARKERS[1])
        if idx_end < 0:
            return {}

        return json.loads(content[idx_begin + len(cls.PATCH_INFO_MARKERS[0]) : idx_end].strip())

    @staticmethod
    def backup_files(files: Iterable[str], force_overwrite: bool = False) -> List[str]:
        ok_files = []

        for file in files:
            file_backup = file + ".bak"

            if os.path.isdir(file_backup):
                continue

            if not os.path.isfile(file_backup) or force_overwrite:
                shutil.copyfile(file, file_backup)
                ok_files.append(file)

        return ok_files

    @staticmethod
    def restore_directory(path: str) -> List[str]:
        if not os.path.isdir(path):
            return []

        ok_files = []

        for dir_path, _, file_names in os.walk(path):
            for file_name in file_names:
                if not file_name.endswith(".bak"):
                    continue

                file_path = os.path.join(dir_path, file_name)
                file_path_original = file_path[:-4]

                shutil.copyfile(file_path, file_path_original)
                ok_files.append(file_path_original)

        return ok_files

    @staticmethod
    def json_dumps_better(value: Any, **kwargs) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, **kwargs)

    @staticmethod
    def file_get_content(path: str, **kwargs) -> Optional[str]:
        kwargs.setdefault("encoding", "utf-8")

        try:
            with io.open(path, "r", **kwargs) as f:
                return f.read()
        except Exception:
            return None

    @staticmethod
    def file_set_content(path: str, content: str, **kwargs) -> bool:
        kwargs.setdefault("encoding", "utf-8")
        kwargs.setdefault("newline", "\n")

        try:
            with io.open(path, "w", **kwargs) as f:
                f.write(content)
                return True
        except Exception:
            return False
