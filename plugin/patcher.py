import datetime
import io
import json
import operator
import os
import re
import shutil

from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple


def now_isoformat() -> str:
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()


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


def json_dumps(value: Any, **kwargs) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, **kwargs)


def file_get_content(path: str, **kwargs) -> Optional[str]:
    try:
        with io.open(path, "r", encoding="utf-8", **kwargs) as f:
            return f.read()
    except Exception:
        return None


def file_set_content(path: str, content: str, **kwargs) -> bool:
    try:
        with io.open(path, "w", encoding="utf-8", newline="\n", **kwargs) as f:
            f.write(content)
            return True
    except Exception:
        return False


class SchemaVersion:
    def __init__(self, major: int = 0, minor: int = 0, patch: int = 0) -> None:
        self.v_tuple = (major, minor, patch)

    def __hash__(self) -> int:
        return self.v_tuple.__hash__()

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return ".".join(map(str, self.v_tuple))

    def __eq__(self, other: object) -> bool:
        return self._compare_2(other, operator.eq)

    def __ge__(self, other: object) -> bool:
        return self._compare_2(other, operator.ge)

    def __gt__(self, other: object) -> bool:
        return self._compare_2(other, operator.gt)

    def __le__(self, other: object) -> bool:
        return self._compare_2(other, operator.le)

    def __lt__(self, other: object) -> bool:
        return self._compare_2(other, operator.lt)

    def __ne__(self, other: object) -> bool:
        return self._compare_2(other, operator.ne)

    def _compare_2(self, other: object, comparator: Callable[[object, object], bool]) -> bool:
        if isinstance(other, self.__class__):
            return comparator(self.v_tuple, other.v_tuple)

        if isinstance(other, str):
            return comparator(self, self.from_str(other))

        raise ValueError("SchemaVersion can only be compared with itself or str.")

    @staticmethod
    def from_str(v_str: str) -> "SchemaVersion":
        m = re.search(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?", v_str.strip())

        if not m:
            raise ValueError("The input is not a valid version string...")

        major = int(m.group(1))
        minor = int(m.group(2) or "0")
        patch = int(m.group(3) or "0")

        return SchemaVersion(major, minor, patch)


class AlreadyPatchedException(Exception):
    def __init__(self, message: str = "") -> None:
        super().__init__(message or '"intelephense" had been patched...')


class Patcher:
    VERSION = SchemaVersion(1, 1, 1)

    PATCH_INFO_MARK_PAIR = ("--- PATCH_INFO_BEGIN ---", "--- PATCH_INFO_END ---")
    PATCHED_MARK_DETECTION = "/** FILE HAS BEEN PATCHED **/"

    PATCHED_MARK = "\n".join(
        [
            # indicates file has been patched
            PATCHED_MARK_DETECTION,
            # patch info
            "/** " + " {info} ".join(PATCH_INFO_MARK_PAIR) + " **/",
        ]
    )

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

        backup_files([path])

        content = file_get_content(path) or ""
        content, occurrences = cls.patch_str(content)

        if occurrences == 0:
            return (False, 0)

        is_success = file_set_content(path, content)

        return (is_success, occurrences)

    @classmethod
    def patch_str(cls, content: str) -> Tuple[str, int]:
        if content.rfind(cls.PATCHED_MARK_DETECTION) > -1:
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
        LICENSE_OBJECT_JS = json_dumps(cls.LICENSE_OBJECT)

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
        return cls.PATCHED_MARK.format(
            info=json_dumps(
                {
                    "patcher": __file__,
                    "version": str(cls.VERSION),
                    "occurrences": occurrences,
                    "time": now_isoformat(),
                },
            ),
        )

    @classmethod
    def extract_patch_info(cls, path_or_content: str) -> Dict[str, Any]:
        content = file_get_content(path_or_content) or path_or_content
        region = [content.rfind(mark) for mark in cls.PATCH_INFO_MARK_PAIR]

        if region[0] < 0 or region[1] < 0:
            return {}

        region[0] += len(cls.PATCH_INFO_MARK_PAIR[0])

        return json.loads(content[slice(*region)].strip())
