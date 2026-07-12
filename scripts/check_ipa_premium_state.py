"""Static audit for Premium-bypass/injection indicators in an IPA.

This tool does not modify the IPA and cannot prove a live entitlement. It
reports evidence that an archive is injected, directly patched, or clean.
"""

from __future__ import annotations

import argparse
import plistlib
from pathlib import Path
import re
import struct
import zipfile


CRACK_MARKERS = re.compile(r"(?:AlightMotionCrack|AMPrem|decrypt\.day|_patched)", re.I)
PRODUCT_RE = re.compile(rb"alightcreative\.motion\.[A-Za-z0-9_.-]+")
PREMIUM_TERMS = (
    b"isPremiumUser", b"isPremium", b"isSubscribed", b"unlockedPremiumUser",
    b"hasActiveSubscription", b"isProUser", b"getAccountStatusAndLicenses",
)
PATCH_WORDS = {
    # mov w0, #0 / mov w0, #1 / ret; useful only as indicators, not proof.
    b"\x00\x00\x80\x52": "mov w0, #0",
    b"\x20\x00\x80\x52": "mov w0, #1",
    b"\xc0\x03\x5f\xd6": "ret",
}


def load_commands(data: bytes) -> list[str]:
    if len(data) < 32 or data[:4] != b"\xcf\xfa\xed\xfe":
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
            name_off = struct.unpack_from("<I", data, cursor + 8)[0]
            start = cursor + name_off
            stop = data.find(b"\0", start, cursor + size)
            if stop < 0:
                stop = cursor + size
            result.append(data[start:stop].decode("utf-8", "replace"))
        cursor += size
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ipa", type=Path)
    args = parser.parse_args()
    if not args.ipa.is_file():
        parser.error(f"not found: {args.ipa}")

    findings: list[tuple[str, str]] = []
    with zipfile.ZipFile(args.ipa, "r") as archive:
        names = archive.namelist()
        if archive.testzip() is not None:
            findings.append(("ERROR", "ZIP archive is corrupt"))
        if len(names) != len(set(names)):
            findings.append(("ERROR", "duplicate ZIP members"))

        app_names = [n for n in names if n.startswith("Payload/") and ".app/" in n]
        executable = next((n for n in app_names if n.endswith("/AlightMotion")), None)
        if executable is None:
            findings.append(("ERROR", "AlightMotion executable not found"))
            print_report(args.ipa, findings, [], [])
            return 2

        main = archive.read(executable)
        dylib_refs = load_commands(main)
        crack_refs = [x for x in dylib_refs if CRACK_MARKERS.search(x)]
        crack_files = [n for n in names if CRACK_MARKERS.search(n)]
        if crack_refs:
            findings.append(("HIGH", f"main executable loads injected library: {crack_refs}"))
        if crack_files:
            findings.append(("HIGH", f"injection/patch artifacts present: {crack_files}"))

        try:
            info_name = executable.rsplit("/", 1)[0] + "/Info.plist"
            info = plistlib.loads(archive.read(info_name))
            findings.append(("INFO", f"bundle={info.get('CFBundleIdentifier')} version={info.get('CFBundleVersion')}"))
        except Exception as exc:
            findings.append(("ERROR", f"cannot parse Info.plist: {exc}"))

        product_ids = sorted({x.decode("ascii", "ignore") for x in PRODUCT_RE.findall(main)})
        premium_hits = sorted({term.decode("ascii") for term in PREMIUM_TERMS if term in main})
        for word, label in PATCH_WORDS.items():
            count = main.count(word)
            if count:
                findings.append(("INFO", f"ARM64 pattern {label}: {count} occurrence(s); context required"))

        print_report(args.ipa, findings, product_ids, premium_hits)

        if not crack_refs and not crack_files:
            print("STATIC VERDICT: no obvious injected-bypass artifact found")
            print("This does not prove Premium is active or that receipts are valid.")
            return 0
        print("STATIC VERDICT: bypass/injection indicators found")
        return 1


def print_report(path: Path, findings: list[tuple[str, str]], products: list[str], premium: list[str]) -> None:
    print(f"IPA: {path}")
    print("Findings:")
    for severity, message in findings:
        print(f"  [{severity}] {message}")
    print(f"Observed product strings: {products or 'none'}")
    print(f"Observed Premium-related symbols: {premium or 'none'}")


if __name__ == "__main__":
    raise SystemExit(main())
