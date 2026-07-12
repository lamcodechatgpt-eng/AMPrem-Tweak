"""Check likely IPA startup failures and static Premium-bypass indicators.

No Windows tool can prove an iOS process will never crash. This checker reports
deterministic archive/loader failures and labels device runtime as UNVERIFIED.
"""

from __future__ import annotations

import argparse
import plistlib
from pathlib import Path
import re
import struct
import zipfile

MARKERS = re.compile(r"(?:AlightMotionCrack|AMPrem|decrypt\.day|_patched)", re.I)


def macho_dependencies(path: Path) -> list[dict[str, str]]:
    data = path.read_bytes()
    if data[:4] != b"\xcf\xfa\xed\xfe":
        return []
    ncmds, sizeofcmds = struct.unpack_from("<II", data, 16)
    cursor = 32
    end = min(len(data), cursor + sizeofcmds)
    result = []
    for _ in range(ncmds):
        if cursor + 8 > end:
            break
        cmd, size = struct.unpack_from("<II", data, cursor)
        if size < 8 or cursor + size > end:
            break
        if cmd in (0xC, 0x18, 0x80000018):
            name_offset = struct.unpack_from("<I", data, cursor + 8)[0]
            start = cursor + name_offset
            stop = data.find(b"\0", start, cursor + size)
            if stop < 0:
                stop = cursor + size
            result.append({"path": data[start:stop].decode("utf-8", "replace")})
        cursor += size
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ipa", type=Path)
    args = parser.parse_args()
    if not args.ipa.is_file():
        parser.error(f"not found: {args.ipa}")

    startup_errors: list[str] = []
    startup_warnings: list[str] = []
    bypass: list[str] = []

    with zipfile.ZipFile(args.ipa, "r") as archive:
        names = archive.namelist()
        if archive.testzip() is not None:
            startup_errors.append("corrupt ZIP member")
        if len(names) != len(set(names)):
            startup_errors.append("duplicate ZIP member")

        app_dirs = sorted({n.split("/", 2)[1] for n in names if n.startswith("Payload/") and ".app/" in n})
        if len(app_dirs) != 1:
            startup_errors.append(f"expected one app bundle, found {app_dirs}")
            print_result(args.ipa, startup_errors, startup_warnings, bypass)
            return 2
        app = f"Payload/{app_dirs[0]}/"

        try:
            info = plistlib.loads(archive.read(app + "Info.plist"))
        except Exception as exc:
            startup_errors.append(f"Info.plist unreadable: {exc}")
            info = {}
        executable_name = app + str(info.get("CFBundleExecutable", ""))
        if executable_name not in names:
            startup_errors.append(f"CFBundleExecutable missing: {executable_name}")
            print_result(args.ipa, startup_errors, startup_warnings, bypass)
            return 2

        main = archive.read(executable_name)
        if main[:4] != b"\xcf\xfa\xed\xfe":
            startup_errors.append("main executable is not arm64 Mach-O")
        else:
            temp = Path(__file__).with_name(".startup_check_macho")
            temp.write_bytes(main)
            try:
                deps = macho_dependencies(temp)
            finally:
                temp.unlink(missing_ok=True)
            for dep in deps:
                path = dep["path"]
                if not path.startswith("@rpath/"):
                    continue
                relative = path.removeprefix("@rpath/")
                if relative.startswith("libswift"):
                    continue
                candidates = [app + "Frameworks/" + relative, app + relative]
                if not any(candidate in names for candidate in candidates):
                    startup_errors.append(f"missing @rpath dependency: {path}")
                if MARKERS.search(path):
                    bypass.append(f"main load command: {path}")

        marker_files = [n for n in names if MARKERS.search(n)]
        bypass.extend(f"archive member: {n}" for n in marker_files)

        if any(n.startswith(app + "_CodeSignature/") for n in names):
            startup_warnings.append("old app CodeResources present; re-signing may replace it")
        else:
            startup_warnings.append("app-level code signature absent; re-sign before install")
        if not any(n.startswith(app + "Frameworks/") for n in names):
            startup_warnings.append("no embedded Frameworks directory")

    print_result(args.ipa, startup_errors, startup_warnings, bypass)
    if startup_errors:
        return 2
    if bypass:
        return 1
    return 0


def print_result(path: Path, errors: list[str], warnings: list[str], bypass: list[str]) -> None:
    print(f"IPA: {path}")
    print("STARTUP:")
    if errors:
        for item in errors:
            print(f"  [FAIL] {item}")
        print("  VERDICT: likely startup failure; device launch not attempted")
    else:
        print("  [PASS] deterministic archive/loader checks")
        print("  VERDICT: no deterministic startup failure found")
    for item in warnings:
        print(f"  [WARN] {item}")
    print("PREMIUM STATIC:")
    if bypass:
        for item in sorted(set(bypass)):
            print(f"  [INDICATOR] {item}")
        print("  VERDICT: bypass/injection indicators found")
    else:
        print("  VERDICT: no obvious bypass/injection artifact")
    print("RUNTIME: UNVERIFIED — requires launch on iOS and verified StoreKit entitlement")


if __name__ == "__main__":
    raise SystemExit(main())
