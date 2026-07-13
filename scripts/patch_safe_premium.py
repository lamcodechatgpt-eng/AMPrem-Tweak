"""Safe patch: only +0x3A (isPremiumUser=true) and +0x39 (isFreeUser=false), skip +0x38."""
import struct, sys

BIN = r'D:\iPA\Alightmotion\AlightMotionMod\V1\extracted\Payload\AlightMotion.app\AlightMotion'
BACKUP = BIN + '.bak'

print("=== Safe Premium Patch (no +0x38) ===\n")

with open(BIN, 'rb') as f:
    data = bytearray(f.read())

# __TEXT,__text bounds
text_start = 0x4000
text_end = 0x2445584

# LDRB <Wt>, [<Xn>, #imm] = 0x39400000 | imm12<<10 | Xn<<5 | Wt
# pattern: 0x3940xxxx -> high 10 bits = 0xE5 (0000 0011 1001 0100 00xx xxxx xxxx xxxx)
LDRB_MASK = 0xFFC00000
LDRB_PAT = 0x39400000

# STRB <Wt>, [<Xn>, #imm] = 0x39000000 | imm12<<10 | Xn<<5 | Wt
STRB_MASK = 0xFFC00000
STRB_PAT = 0x39000000

# MOV <Wd>, #1 = 0x52800020 | Rd
MOV1_BASE = 0x52800020
# MOV <Wd>, #0 = 0x52800000 | Rd (actually 0x52800000 | Rd for MOV Wd, #0)
# Wait: MOV Wd, #0 is encoded as MOVZ Wd, #0 which is 0x52800000 | Rd
# Let me use a simpler approach: MOV Wd, #1 = 0x52800020 | Rd, MOV Wd, #0 = 0x52800000 | Rd

def patch_offset(data, offset, imm, patches):
    """Patch LDRB at offset (returns updated bytearray, list of patches)"""
    total = 0
    pos = text_start
    while pos < text_end:
        val = struct.unpack_from('<I', data, pos)[0]
        if (val & LDRB_MASK) == LDRB_PAT:
            imm12 = (val >> 10) & 0xFFF
            if imm12 == offset:
                rd = val & 0x1F
                if offset == 0x3A:
                    # isPremiumUser -> MOV Wd, #1
                    new_val = MOV1_BASE | rd
                else:
                    # isFreeUser -> MOV Wd, #0
                    new_val = 0x52800000 | rd
                struct.pack_into('<I', data, pos, new_val)
                total += 1
        pos += 4
    return total

# Patch +0x3A: isPremiumUser -> true
n_3a = 0
pos = text_start
while pos < text_end:
    val = struct.unpack_from('<I', data, pos)[0]
    if (val & LDRB_MASK) == LDRB_PAT:
        imm12 = (val >> 10) & 0xFFF
        if imm12 == 0x3A:
            rd = val & 0x1F
            struct.pack_into('<I', data, pos, 0x52800020 | rd)
            n_3a += 1
    pos += 4

# Patch +0x39: isFreeUser -> false
n_39_read = 0
pos = text_start
while pos < text_end:
    val = struct.unpack_from('<I', data, pos)[0]
    if (val & LDRB_MASK) == LDRB_PAT:
        imm12 = (val >> 10) & 0xFFF
        if imm12 == 0x39:
            rd = val & 0x1F
            struct.pack_into('<I', data, pos, 0x52800000 | rd)
            n_39_read += 1
    pos += 4

# Patch STRB +0x39: block writes
n_39_write = 0
pos = text_start
while pos < text_end:
    val = struct.unpack_from('<I', data, pos)[0]
    if (val & STRB_MASK) == STRB_PAT:
        imm12 = (val >> 10) & 0xFFF
        if imm12 == 0x39:
            rd = val & 0x1F
            # NOP
            struct.pack_into('<I', data, pos, 0xD503201F)
            n_39_write += 1
    pos += 4

# Write patched binary
out_path = BIN
with open(out_path, 'wb') as f:
    f.write(data)

print(f"  +0x3A (isPremiumUser=true):  {n_3a} LDRB patched")
print(f"  +0x39 (isFreeUser=false):    {n_39_read} LDRB + {n_39_write} STRB patched")
print(f"  +0x38 (isSpooner):           SKIPPED")
print(f"\nTotal: {n_3a + n_39_read + n_39_write} patches")
print("Binary ready!")
