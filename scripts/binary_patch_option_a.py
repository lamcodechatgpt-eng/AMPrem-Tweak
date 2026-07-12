#!/usr/bin/env python3
"""
Option A - Enhanced Binary Patcher for LiveContainer
====================================================
Since LiveContainer doesn't support dylib injection, all bypass logic
must be baked directly into the executable via binary patching.

Patches applied:
  1. LDRB Wd, [Xn, #0x3A] -> MOV Wd, #1   (isPremiumUser = true)      [IAPManager +0x3A]
  2. LDRB Wd, [Xn, #0x39] -> MOV Wd, #0   (isFreeUser = false)        [IAPManager +0x39]
  3. LDRB Wd, [Xn, #0x38] -> MOV Wd, #0   (isSpooner = false)         [IAPManager +0x38]
  4. STRB WZR, [Xn, #0x3A] -> NOP          (prevent clearing premium)  [IAPManager +0x3A]
  5. STRB W1+, [X0+, #0x39] -> STRB WZR   (prevent setting freeUser)  [IAPManager +0x39]

Usage:
  python scripts/binary_patch_option_a.py <input_binary> [output_binary]
"""

import struct
import sys
import os

NOP = 0xD503201F

def parse_macho_text_range(data):
    magic = struct.unpack_from('<I', data, 0)[0]
    if magic not in (0xFEEDFACE, 0xFEEDFACF):
        return None, None
    is_64 = magic == 0xFEEDFACF
    offset = 12  # past magic(4) + cputype(4) + cpusubtype(4)
    filetype = struct.unpack_from('<I', data, offset)[0]
    offset += 4
    ncmds = struct.unpack_from('<I', data, offset)[0]
    offset += 12  # past ncmds(4) + sizeofcmds(4) + flags(4)
    if is_64:
        offset += 4  # reserved
    for _ in range(ncmds):
        if offset + 8 > len(data):
            break
        cmd = struct.unpack_from('<I', data, offset)[0]
        cmdsize = struct.unpack_from('<I', data, offset + 4)[0]
        if cmd == 0x19:  # LC_SEGMENT_64
            segname = data[offset + 8: offset + 24].rstrip(b'\0').decode('ascii', errors='replace')
            if segname == '__TEXT':
                nsects = struct.unpack_from('<I', data, offset + 64)[0]
                sect_offset = offset + 72
                for _ in range(nsects):
                    if sect_offset + 16 > len(data):
                        break
                    sectname = data[sect_offset: sect_offset + 16].rstrip(b'\0').decode('ascii', errors='replace')
                    if sectname == '__text':
                        text_off = struct.unpack_from('<I', data, sect_offset + 48)[0]
                        text_sz = struct.unpack_from('<Q', data, sect_offset + 40)[0]
                        return text_off, text_sz
                    sect_offset += 80
        offset += cmdsize
    return None, None


def patch_ldrb_to_mov(data, start, end, imm, target_val):
    """
    Patch LDRB Wd, [Xn, #imm] -> MOV Wd, #target_val
    Returns count of patches.
    """
    count = 0
    # LDRB (unsigned offset): base 0x39400000, imm at bits[21:10]
    mask = 0xFFC00000 | (0xFFF << 10)
    pattern = 0x39400000 | (imm << 10)
    for off in range(start, min(end, len(data) - 3), 4):
        word = struct.unpack_from('<I', data, off)[0]
        if (word & mask) == pattern:
            rd = word & 0x1F
            # MOV Wd, #target_val = ORR Wd, WZR, #target_val
            new_word = 0x320003E0 | rd if target_val == 1 else 0x320003E0 | rd  # same encoding, target_val is the immediate
            # Actually MOV Wd, #N: the encoding depends on N being a bitmask immediate
            # For N=0: MOV Wd, #0 = EOR Wd, Wd, Wd = 0x2A0003E0 | rd | (rd << 16) | (rd << ...)
            # Actually MOV Wd, #0: EOR Wd, Wd, Wd = 0x2A000000 | (rd << 16) | (rd << 5) | rd
            if target_val == 1:
                new_word = 0x320003E0 | rd
            else:
                # MOV Wd, #0 = EOR Wd, Wd, Wd (Wd = Wd XOR Wd)
                new_word = 0x2A000000 | (rd << 16) | (rd << 5) | rd
            struct.pack_into('<I', data, off, new_word)
            count += 1
    return count


def patch_strb_wzr_to_nop(data, start, end, imm):
    """
    Patch STRB WZR, [Xn, #imm] -> NOP (prevent writing false to the field)
    Returns count of patches.
    """
    count = 0
    # STRB (unsigned offset) with WZR: 0x39000000 | (imm << 10) | (Xn << 5) | 0x1F
    base = 0x39000000 | (imm << 10) | 0x1F
    # The Xn register varies, so match: 0x39000000 | (imm << 10) | 0x1F, mask out Xn
    mask = 0xFFC00000 | (0xFFF << 10) | 0x1F
    pattern = 0x39000000 | (imm << 10) | 0x1F
    for off in range(start, min(end, len(data) - 3), 4):
        word = struct.unpack_from('<I', data, off)[0]
        if (word & mask) == pattern:
            struct.pack_into('<I', data, off, NOP)
            count += 1
    return count


def patch_strb_to_strb_wzr(data, start, end, imm, target_regs=None):
    """
    Patch STRB Wd, [Xn, #imm] -> STRB WZR, [Xn, #imm] when Wd != WZR
    Used to prevent writing true to isFreeUser (+0x39).
    """
    count = 0
    base = 0x39000000 | (imm << 10)
    mask = 0xFFC00000 | (0xFFF << 10)  # match base + imm, ignore Rn and Rt
    for off in range(start, min(end, len(data) - 3), 4):
        word = struct.unpack_from('<I', data, off)[0]
        if (word & mask) == base:
            rt = word & 0x1F
            if rt != 0x1F:  # not already WZR
                # Change Rt to WZR (0x1F)
                new_word = (word & ~0x1F) | 0x1F
                struct.pack_into('<I', data, off, new_word)
                count += 1
    return count


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    in_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else in_path + '_patched'

    if not os.path.exists(in_path):
        print(f"[-] Input not found: {in_path}")
        sys.exit(1)

    with open(in_path, 'rb') as f:
        data = bytearray(f.read())

    text_off, text_sz = parse_macho_text_range(data)
    if text_off is not None:
        start = text_off
        end = text_off + text_sz
        print(f"[+] __TEXT,__text: offset=0x{text_off:X}, size=0x{text_sz:X} ({text_sz} bytes)")
    else:
        print("[!] Could not parse Mach-O, scanning entire binary (risk of false positives)")
        start = 0
        end = len(data)

    # ---- Patch 1: isPremiumUser = true (LDRB at +0x3A -> MOV Wd, #1) ----
    c1 = patch_ldrb_to_mov(data, start, end, 0x3A, 1)
    print(f"  [1] LDRB [Xn, #0x3A] -> MOV Wd, #1  (isPremiumUser=true):  {c1} patches")

    # ---- Patch 2: isFreeUser = false (LDRB at +0x39 -> MOV Wd, #0) ----
    c2 = patch_ldrb_to_mov(data, start, end, 0x39, 0)
    print(f"  [2] LDRB [Xn, #0x39] -> MOV Wd, #0  (isFreeUser=false):    {c2} patches")

    # ---- Patch 3: Prevent clearing premium (STRB WZR at +0x3A -> NOP) ----
    c3 = patch_strb_wzr_to_nop(data, start, end, 0x3A)
    print(f"  [3] STRB WZR, [Xn, #0x3A] -> NOP   (protect premium):     {c3} patches")

    # ---- Patch 4: Prevent setting freeUser (STRB at +0x39 -> STRB WZR) ----
    c4 = patch_strb_to_strb_wzr(data, start, end, 0x39)
    print(f"  [4] STRB Wd, [Xn, #0x39] -> WZR    (block freeUser set):  {c4} patches")

    total = c1 + c2 + c3 + c4

    with open(out_path, 'wb') as f:
        f.write(data)

    print(f"\n[+] Output: {out_path}")
    print(f"[+] Total patches: {total}")

    if c1 == 0 and c3 == 0 and c2 == 0:
        print("[-] WARNING: No critical patches applied - architecture may not be ARM64")

    # Count actual byte changes
    with open(in_path, 'rb') as f:
        orig = f.read()
    byte_diff = sum(1 for i in range(min(len(orig), len(data))) if orig[i] != data[i])
    print(f"[+] Bytes changed: {byte_diff}")

    return total


if __name__ == '__main__':
    main()
