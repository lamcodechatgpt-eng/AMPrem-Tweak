#!/usr/bin/env python3
"""
Rename the app from "Alight Motion" to "Ultra Motion".
Updates Info.plist + all .strings / .stringsdict + permission descriptions.

Usage:
  python scripts/rename_ultra_motion.py
"""

import os
import re
import plistlib
import struct
import shutil

APP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "extracted", "Payload", "AlightMotion.app")

OLD_NAME = "Alight Motion"
NEW_NAME = "Ultra Motion"
OLD_EXEC = "AlightMotion"
NEW_EXEC = "UltraMotion"

def is_binary_plist(path):
    with open(path, 'rb') as f:
        magic = f.read(8)
        return magic.startswith(b'bplist00')

def replace_in_text_file(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    if OLD_NAME not in content:
        return False
    new_content = content.replace(OLD_NAME, NEW_NAME)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return True


def replace_in_binary_strings(path):
    """Replace string values in binary .strings files (bplist)."""
    with open(path, 'rb') as f:
        data = f.read()

    old_bytes = OLD_NAME.encode('utf-16-be')
    new_bytes = NEW_NAME.encode('utf-16-be')
    new_data = data.replace(new_bytes, new_bytes)  # keep same for now

    if old_bytes not in data:
        return False

    new_data = data.replace(old_bytes, new_bytes)
    with open(path, 'wb') as f:
        f.write(new_data)
    return True


def replace_in_stringsdict(path):
    """Replace in .stringsdict XML files."""
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    if OLD_NAME not in content:
        return False
    new_content = content.replace(OLD_NAME, NEW_NAME)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return True


def update_info_plist(path):
    with open(path, 'rb') as f:
        data = f.read()

    # Read as XML
    text = data.decode('utf-8')
    if OLD_NAME not in text:
        print("  [!] 'Alight Motion' not found in Info.plist")
        return False

    # Replace in XML text form to preserve structure
    text = text.replace(OLD_NAME, NEW_NAME)
    text = text.replace("Alight Motion needs", "Ultra Motion needs")
    text = text.replace("Alight Motion needs", "Ultra Motion needs")

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

    # Verify it's still valid plist
    try:
        plistlib.loads(text.encode('utf-8'))
        print("  [OK] Info.plist is valid")
        return True
    except Exception as e:
        print(f"  [ERROR] Invalid plist after rename: {e}")
        return False


def rename_bundle_dirs():
    """Rename AlightMotion_*.bundle directories to UltraMotion_*.bundle"""
    count = 0
    for entry in os.listdir(APP_DIR):
        if entry.startswith("AlightMotion_") and entry.endswith(".bundle"):
            old_path = os.path.join(APP_DIR, entry)
            new_name = entry.replace("AlightMotion_", "UltraMotion_", 1)
            new_path = os.path.join(APP_DIR, new_name)
            if not os.path.exists(new_path):
                os.rename(old_path, new_path)
                count += 1
    return count


def main():
    print(f"[*] Renaming '{OLD_NAME}' -> '{NEW_NAME}'")
    print(f"[*] App directory: {APP_DIR}")
    print()

    # 1. Update Info.plist
    info_plist = os.path.join(APP_DIR, "Info.plist")
    if os.path.exists(info_plist):
        print("[1] Updating Info.plist...")
        update_info_plist(info_plist)
    else:
        print("[1] Info.plist not found!")

    # 2. Update all .strings files
    print("\n[2] Updating .strings files...")
    strings_count = 0
    for root, dirs, files in os.walk(APP_DIR):
        for f in files:
            path = os.path.join(root, f)
            if f.endswith('.strings'):
                try:
                    if is_binary_plist(path):
                        if replace_in_binary_strings(path):
                            strings_count += 1
                            print(f"     [bin] {os.path.relpath(path, APP_DIR)}")
                    else:
                        if replace_in_text_file(path):
                            strings_count += 1
                            print(f"     [txt] {os.path.relpath(path, APP_DIR)}")
                except Exception as e:
                    print(f"     [ERR] {os.path.relpath(path, APP_DIR)}: {e}")
            elif f.endswith('.stringsdict'):
                try:
                    if replace_in_stringsdict(path):
                        strings_count += 1
                        print(f"     [dict] {os.path.relpath(path, APP_DIR)}")
                except Exception as e:
                    print(f"     [ERR] {os.path.relpath(path, APP_DIR)}: {e}")

    print(f"     Total files updated: {strings_count}")

    print(f"\n[*] Done! Updated {strings_count} resource files.")
    print("[*] Bundle directories and executable name NOT changed (would break app).")
    print("[*] On iOS home screen, the app will show 'Ultra Motion' via CFBundleDisplayName.")

if __name__ == '__main__':
    main()
